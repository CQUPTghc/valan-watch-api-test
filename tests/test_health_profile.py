"""健康档案：读回验证、边界值和失败后的数据恢复。"""

import pytest

from common.api_client import ApiClient
from common.assertions import assert_api_response, assert_rejected
from config.settings import BASE_URL


PROFILE_PATH = "/api/v1/health/profile"


def _get_profile(auth_client, case_id):
    response = auth_client.get(PROFILE_PATH)
    assert_api_response(response, case_id, data_type=dict)
    return response.json()["data"]


def _restore_if_changed(auth_client, field, original, case_id):
    current = _get_profile(auth_client, f"{case_id}-CLEANUP-READ").get(field)
    if current == original:
        return
    response = auth_client.put(PROFILE_PATH, json={field: original})
    assert_api_response(response, f"{case_id}-CLEANUP-WRITE")
    restored = _get_profile(auth_client, f"{case_id}-CLEANUP-VERIFY").get(field)
    assert restored == original, (
        f"{case_id} 恢复失败：字段={field}，原值={original!r}，当前值={restored!r}"
    )


def _assert_bmi(profile, case_id):
    height = profile.get("height")
    weight = profile.get("weight")
    bmi = profile.get("bmi")
    assert isinstance(height, (int, float)) and height > 0, (
        f"{case_id} 无法计算 BMI：height={height!r}"
    )
    assert isinstance(weight, (int, float)) and weight > 0, (
        f"{case_id} 无法计算 BMI：weight={weight!r}"
    )
    assert isinstance(bmi, (int, float)), f"{case_id} BMI 类型错误：{type(bmi).__name__}"
    expected = round(weight / ((height / 100) ** 2), 2)
    assert bmi == pytest.approx(expected, abs=0.01), (
        f"{case_id} BMI 未随档案更新：height={height}，weight={weight}，"
        f"预期={expected}，实际={bmi}"
    )


def _update_and_verify(auth_client, field, value, case_id):
    original_profile = _get_profile(auth_client, f"{case_id}-BEFORE")
    original = original_profile.get(field)
    if original is None:
        pytest.skip(f"{case_id} 原字段 {field} 为空，无法保证通过 PUT 恢复原状态")
    if value == original:
        pytest.skip(f"{case_id} 目标值与原值相同，无法验证持久化")
    try:
        update = auth_client.put(PROFILE_PATH, json={field: value})
        assert_api_response(update, case_id, data_type=dict)
        put_profile = update.json()["data"]
        assert put_profile.get(field) == value, (
            f"{case_id} PUT 返回值未更新：字段={field}，"
            f"预期={value!r}，实际={put_profile.get(field)!r}"
        )
        current = _get_profile(auth_client, f"{case_id}-AFTER")
        assert current.get(field) == value, (
            f"{case_id} GET 读回未持久化：字段={field}，"
            f"预期={value!r}，实际={current.get(field)!r}"
        )
        # BUG-HP-001 的回归：PUT 的完整档案与随后 GET 不得出现同版本字段不一致。
        for key in ("height", "weight", "bmi", "bloodType"):
            if key in put_profile and key in current:
                assert put_profile[key] == current[key], (
                    f"{case_id} PUT/GET 字段不一致：{key}，"
                    f"PUT={put_profile[key]!r}，GET={current[key]!r}"
                )
        if field in ("height", "weight"):
            _assert_bmi(current, case_id)
    finally:
        _restore_if_changed(auth_client, field, original, case_id)


@pytest.mark.health
@pytest.mark.smoke
def test_get_health_profile(auth_client):
    """HP-001：档案结构与当前登录用户的健康字段。"""
    profile = _get_profile(auth_client, "HP-001")
    for key in ("height", "weight", "bmi", "hasContent"):
        assert key in profile, f"HP-001 健康档案缺少 {key} 字段"
    assert isinstance(profile["hasContent"], bool), "HP-001 hasContent 应为布尔值"
    if profile["hasContent"]:
        _assert_bmi(profile, "HP-001")


@pytest.mark.health
@pytest.mark.parametrize(
    "case_id, token",
    [("HP-003", None), ("HP-INVALID-TOKEN", "Bearer invalid-access-token")],
    ids=["HP-003-no-token", "HP-INVALID-TOKEN"],
)
def test_get_profile_rejects_unauthorized(client, case_id, token):
    headers = {"Authorization": token} if token else {}
    isolated = ApiClient(BASE_URL)
    try:
        response = isolated.get(PROFILE_PATH, headers=headers)
    finally:
        isolated.session.close()
    body = response.json()
    assert body.get("data") is None, f"{case_id} 未认证仍返回健康档案"
    assert_rejected(response, case_id, expected_status=401)


@pytest.mark.health
@pytest.mark.parametrize(
    "field, delta, case_id",
    [("height", 1, "HP-002-HEIGHT"), ("weight", 1, "HP-002-WEIGHT")],
    ids=["update-height", "update-weight"],
)
def test_update_health_profile_field(auth_client, field, delta, case_id):
    profile = _get_profile(auth_client, f"{case_id}-SELECT")
    original = profile.get(field)
    if not isinstance(original, (int, float)):
        pytest.skip(f"{case_id} 当前 {field} 不为数字，无法安全构造并恢复")
    upper = 250 if field == "height" else 300
    lower = 50 if field == "height" else 20
    new_value = original + delta if original + delta <= upper else original - delta
    if not lower <= new_value <= upper:
        pytest.skip(f"{case_id} 当前 {field} 超出文档范围，无法安全构造测试值")
    _update_and_verify(auth_client, field, new_value, case_id)


@pytest.mark.health
@pytest.mark.parametrize(
    "field, value, valid, case_id, known_bug",
    [
        ("height", 49, False, "HP-HEIGHT-49", False),
        pytest.param("height", 50, True, "HP-HEIGHT-50", True, marks=pytest.mark.known_bug),
        ("height", 250, True, "HP-HEIGHT-250", False),
        ("height", 251, False, "HP-HEIGHT-251", False),
        ("weight", 19, False, "HP-WEIGHT-19", False),
        ("weight", 20, True, "HP-WEIGHT-20", False),
        pytest.param("weight", 300, True, "HP-WEIGHT-300", True, marks=pytest.mark.known_bug),
        ("weight", 301, False, "HP-WEIGHT-301", False),
        ("lifestyleSmoking", -1, False, "HP-SMOKING--1", False),
        ("lifestyleSmoking", 0, True, "HP-SMOKING-0", False),
        ("lifestyleSmoking", 1, True, "HP-SMOKING-1", False),
        ("lifestyleSmoking", 2, False, "HP-SMOKING-2", False),
        ("lifestyleDrinking", -1, False, "HP-DRINKING--1", False),
        ("lifestyleDrinking", 0, True, "HP-DRINKING-0", False),
        ("lifestyleDrinking", 2, True, "HP-DRINKING-2", False),
        ("lifestyleDrinking", 3, False, "HP-DRINKING-3", False),
    ],
    ids=[
        "HP-HEIGHT-49", "HP-HEIGHT-50", "HP-HEIGHT-250", "HP-HEIGHT-251",
        "HP-WEIGHT-19", "HP-WEIGHT-20", "HP-WEIGHT-300", "HP-WEIGHT-301",
        "HP-SMOKING--1", "HP-SMOKING-0", "HP-SMOKING-1", "HP-SMOKING-2",
        "HP-DRINKING--1", "HP-DRINKING-0", "HP-DRINKING-2", "HP-DRINKING-3",
    ],
)
def test_health_profile_boundaries(auth_client, field, value, valid, case_id, known_bug):
    """文档规定的身高、体重和生活方式数值边界。"""
    original = _get_profile(auth_client, f"{case_id}-BEFORE").get(field)
    if original is None:
        pytest.skip(f"{case_id} 原字段为空，无法保证恢复")
    if valid and original == value:
        pytest.skip(f"{case_id} 已处于目标边界值，不能验证实际修改")
    try:
        response = auth_client.put(PROFILE_PATH, json={field: value})
        current = _get_profile(auth_client, f"{case_id}-AFTER").get(field)
        if known_bug and response.status_code == 500:
            assert current == original, (
                f"{case_id} 已知 500 发生后数据仍被修改：原值={original!r}，现值={current!r}"
            )
            pytest.xfail(f"{case_id} 已提交后端：合法边界值实际返回 HTTP 500")
        if valid:
            assert_api_response(response, case_id, data_type=dict)
            assert current == value, (
                f"{case_id} 合法边界值未保存：预期={value!r}，实际={current!r}"
            )
            if field in ("height", "weight"):
                _assert_bmi(_get_profile(auth_client, f"{case_id}-BMI"), case_id)
        else:
            assert_rejected(response, case_id, expected_status=400)
            assert current == original, (
                f"{case_id} 非法边界值被写入：原值={original!r}，实际={current!r}"
            )
    finally:
        _restore_if_changed(auth_client, field, original, case_id)


@pytest.mark.health
@pytest.mark.parametrize(
    "field, value, case_id",
    [
        ("height", 0, "HP-HEIGHT-ZERO"),
        ("weight", -1, "HP-WEIGHT-NEGATIVE"),
        ("height", "invalid", "HP-HEIGHT-TYPE"),
        ("weight", "invalid", "HP-WEIGHT-TYPE"),
        ("bloodSugarFasting", 0, "HP-BLOOD-SUGAR-ZERO"),
        ("bloodType", "C", "HP-BLOOD-TYPE-INVALID"),
        ("lifestyleExerciseFrequency", "daily", "HP-EXERCISE-INVALID"),
    ],
    ids=[
        "height-zero", "weight-negative", "height-wrong-type",
        "weight-wrong-type", "blood-sugar-zero", "blood-type-invalid",
        "exercise-enum-invalid",
    ],
)
def test_health_profile_rejects_invalid_values(auth_client, field, value, case_id):
    """非法参数应返回校验错误，档案不能改变。"""
    original = _get_profile(auth_client, f"{case_id}-BEFORE").get(field)
    if original is None:
        pytest.skip(f"{case_id} 原字段为空，无法保证异常请求后恢复")
    try:
        response = auth_client.put(PROFILE_PATH, json={field: value})
        assert_rejected(response, case_id, expected_status=400)
        current = _get_profile(auth_client, f"{case_id}-AFTER").get(field)
        assert current == original, (
            f"{case_id} 非法参数改变了档案：字段={field}，"
            f"原值={original!r}，实际={current!r}"
        )
    finally:
        _restore_if_changed(auth_client, field, original, case_id)
