"""P1 personal information and settings contracts."""

import pytest

from common.assertions import assert_api_response, assert_rejected


PROFILE = "/api/v1/user/profile"
SETTINGS = "/api/v1/user/settings"
EMERGENCY_CONTACTS = "/api/v1/user/emergency-contacts"


def _read(auth_client, path, case_id):
    return assert_api_response(
        auth_client.get(path), case_id, data_type=dict
    )


def _restore_if_changed(auth_client, path, field, original, case_id):
    current = _read(auth_client, path, f"{case_id}-恢复前查询")
    if current.get(field) == original:
        return
    assert_api_response(
        auth_client.put(path, json={field: original}),
        f"{case_id}-恢复", data_type=dict,
    )
    restored = _read(auth_client, path, f"{case_id}-恢复校验")
    assert restored.get(field) == original, (
        f"{case_id} 测试数据恢复失败：字段={field}，"
        f"预期原值={original!r}，实际={restored.get(field)!r}"
    )


@pytest.mark.user
@pytest.mark.smoke
def test_get_user_profile(auth_client):
    data = _read(auth_client, PROFILE, "USER-GET-001")
    assert isinstance(data.get("id"), int), "USER-GET-001 用户 id 应为整数"
    assert isinstance(data.get("memberId"), str) and data["memberId"], (
        "USER-GET-001 memberId 应为非空字符串"
    )
    if data.get("roles") is not None:
        assert isinstance(data["roles"], list), (
            "USER-GET-001 roles 非空时应为数组"
        )


@pytest.mark.user
@pytest.mark.smoke
def test_get_user_settings(auth_client):
    data = _read(auth_client, SETTINGS, "USER-SET-001")
    for field in ("fontSize", "elderlyMode", "notificationEnabled"):
        assert field in data, f"USER-SET-001 设置缺少 {field} 字段"
    assert data["fontSize"] in ("small", "medium", "large"), (
        f"USER-SET-001 fontSize 非法：{data['fontSize']!r}"
    )
    for field in ("elderlyMode", "notificationEnabled"):
        assert data[field] in (0, 1), (
            f"USER-SET-001 {field} 应为 0 或 1，实际={data[field]!r}"
        )


@pytest.mark.user
def test_get_emergency_contacts(auth_client):
    case_id = "USER-EMERGENCY-GET"
    data = _read(auth_client, EMERGENCY_CONTACTS, case_id)
    assert isinstance(data.get("contacts"), list), (
        f"{case_id} contacts 应为数组，实际={type(data.get('contacts')).__name__}"
    )
    assert len(data["contacts"]) <= 3, (
        f"{case_id} 紧急联系人超过文档上限 3，实际={len(data['contacts'])}"
    )
    assert isinstance(data.get("editable"), bool), (
        f"{case_id} editable 应为布尔值"
    )
    for index, contact in enumerate(data["contacts"]):
        assert isinstance(contact, dict), f"{case_id} 第{index}位联系人不是对象"
        assert isinstance(contact.get("contactId"), int), (
            f"{case_id} 第{index}位联系人缺少整数 contactId"
        )
        assert isinstance(contact.get("maskedPhone"), str), (
            f"{case_id} 第{index}位联系人缺少 maskedPhone"
        )
        assert contact.get("relationCode") in {
            "SPOUSE", "PARENT", "CHILD", "SIBLING", "OTHER"
        }, f"{case_id} 第{index}位联系人关系枚举非法"
        assert isinstance(contact.get("sortOrder"), int) and 0 <= contact["sortOrder"] <= 2, (
            f"{case_id} 第{index}位联系人排序超出 0～2"
        )


@pytest.mark.user
@pytest.mark.smoke
@pytest.mark.parametrize(
    "path", [PROFILE, SETTINGS, EMERGENCY_CONTACTS],
    ids=["profile", "settings", "emergency-contacts"],
)
def test_user_endpoint_requires_login(client, path):
    assert_rejected(
        client.get(path), f"USER-AUTH-{path.rsplit('/', 1)[-1]}",
        expected_status=401,
    )


@pytest.mark.user
def test_update_nickname_round_trip(auth_client):
    case_id = "USER-PUT-001"
    before = _read(auth_client, PROFILE, f"{case_id}-原值")
    original = before.get("nickname")
    if not isinstance(original, str) or not original:
        pytest.skip("原昵称为空；当前接口契约未说明如何恢复为空昵称")
    changed = "API校验" if original != "API校验" else "API检查"
    try:
        assert_api_response(
            auth_client.put(PROFILE, json={"nickname": changed}),
            case_id, data_type=dict,
        )
        actual = _read(auth_client, PROFILE, f"{case_id}-修改后查询")
        assert actual.get("nickname") == changed, (
            f"{case_id} 昵称未真正保存：预期={changed!r}，"
            f"实际={actual.get('nickname')!r}"
        )
    finally:
        _restore_if_changed(auth_client, PROFILE, "nickname", original, case_id)


@pytest.mark.user
def test_update_font_size_round_trip(auth_client):
    case_id = "USER-SET-002"
    before = _read(auth_client, SETTINGS, f"{case_id}-原值")
    original = before.get("fontSize")
    assert original in ("small", "medium", "large"), (
        f"{case_id} 原 fontSize 不符合契约：{original!r}"
    )
    changed = "large" if original != "large" else "medium"
    try:
        assert_api_response(
            auth_client.put(SETTINGS, json={"fontSize": changed}),
            case_id, data_type=dict,
        )
        actual = _read(auth_client, SETTINGS, f"{case_id}-修改后查询")
        assert actual.get("fontSize") == changed, (
            f"{case_id} fontSize 未真正保存：预期={changed!r}，"
            f"实际={actual.get('fontSize')!r}"
        )
    finally:
        _restore_if_changed(auth_client, SETTINGS, "fontSize", original, case_id)


@pytest.mark.user
@pytest.mark.parametrize(
    "field,value", [
        ("nickname", "A"),
        ("nickname", "A" * 21),
        ("gender", -1),
        ("gender", 3),
    ], ids=["nickname-short", "nickname-long", "gender-below", "gender-above"],
)
def test_update_user_profile_rejects_invalid(auth_client, field, value):
    case_id = f"USER-INVALID-{field}-{value!r}"
    before = _read(auth_client, PROFILE, f"{case_id}-原值")
    original = before.get(field)
    if original is None:
        pytest.skip(f"{case_id} 原字段为空，接口未定义恢复为 null 的写法")
    try:
        assert_rejected(
            auth_client.put(PROFILE, json={field: value}), case_id,
            expected_status=400,
        )
        actual = _read(auth_client, PROFILE, f"{case_id}-拒绝后查询")
        assert actual.get(field) == original, (
            f"{case_id} 非法参数仍修改了资料："
            f"原值={original!r}，实际={actual.get(field)!r}"
        )
    finally:
        _restore_if_changed(auth_client, PROFILE, field, original, case_id)


@pytest.mark.user
@pytest.mark.parametrize(
    "field,value", [
        ("fontSize", "giant"),
        ("elderlyMode", -1),
        ("elderlyMode", 2),
    ], ids=["font-size-enum", "elderly-mode-below", "elderly-mode-above"],
)
def test_update_settings_rejects_invalid(auth_client, field, value):
    case_id = f"USER-SET-INVALID-{field}-{value!r}"
    before = _read(auth_client, SETTINGS, f"{case_id}-原值")
    original = before.get(field)
    if original is None:
        pytest.skip(f"{case_id} 原设置为空，接口未定义恢复为 null 的写法")
    try:
        assert_rejected(
            auth_client.put(SETTINGS, json={field: value}), case_id,
            expected_status=400,
        )
        actual = _read(auth_client, SETTINGS, f"{case_id}-拒绝后查询")
        assert actual.get(field) == original, (
            f"{case_id} 非法参数仍修改了设置："
            f"原值={original!r}，实际={actual.get(field)!r}"
        )
    finally:
        _restore_if_changed(auth_client, SETTINGS, field, original, case_id)


@pytest.mark.user
@pytest.mark.manual
def test_replace_emergency_contacts_requires_restorable_fixture():
    pytest.skip(
        "紧急联系人 GET 仅返回脱敏手机号，无法由当前响应构造完整原值并安全恢复 PUT replace"
    )
