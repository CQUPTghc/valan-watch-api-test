"""P1 health portrait read contracts; generation remains an external check."""

import pytest

from common.assertions import assert_rejected, safe_response_text


def _raw_get(auth_client, path, case_id, params=None):
    response = auth_client.get(path, params=params)
    if response.status_code == 503:
        pytest.skip(f"{case_id} 心泰画像服务当前不可用（HTTP 503）")
    assert response.status_code == 200, (
        f"{case_id} HTTP状态异常：预期=200，实际={response.status_code}，"
        f"响应={safe_response_text(response)}"
    )
    try:
        return response.json()  # Portrait endpoints return raw JSON, not Result.
    except ValueError as exc:
        raise AssertionError(
            f"{case_id} 响应不是 JSON：{safe_response_text(response)}"
        ) from exc


@pytest.mark.portrait
@pytest.mark.external
def test_portrait_page(auth_client):
    case_id = "PORTRAIT-PAGE"
    data = _raw_get(auth_client, "/api/v1/health/portrait", case_id)
    assert isinstance(data, dict), f"{case_id} 响应应为对象，实际={type(data).__name__}"
    assert not {"code", "message", "data"}.issubset(data), (
        f"{case_id} OpenAPI 定义原生 HealthPortraitPageResponse，"
        "实际返回了 Result 包装对象"
    )
    # OpenAPI 没有 required 列表；字段出现时仍须符合声明类型。
    for field, expected_type in (("metricGroups", list), ("sourceStatus", dict)):
        if field in data:
            assert isinstance(data[field], expected_type), (
                f"{case_id} {field} 类型异常：预期={expected_type.__name__}，"
                f"实际={type(data[field]).__name__}"
            )


@pytest.mark.portrait
@pytest.mark.external
def test_portrait_history(auth_client):
    case_id = "PORTRAIT-HISTORY"
    history = _raw_get(auth_client,
                       "/api/v1/health/portrait/interpretations", case_id)
    assert isinstance(history, list), (
        f"{case_id} 响应应为数组，实际={type(history).__name__}"
    )
    for month in history:
        assert isinstance(month, dict) and isinstance(
            month.get("healthProfileAnalysisList"), list
        ), f"{case_id} 历史分组缺少 healthProfileAnalysisList 数组"


@pytest.mark.portrait
@pytest.mark.external
def test_portrait_interpretation_detail_when_available(auth_client):
    history = _raw_get(auth_client,
                       "/api/v1/health/portrait/interpretations",
                       "PORTRAIT-HISTORY-FOR-DETAIL")
    if not isinstance(history, list):
        pytest.fail("PORTRAIT-HISTORY-FOR-DETAIL 响应应为数组")
    records = [record for group in history if isinstance(group, dict)
               for record in group.get("healthProfileAnalysisList", [])
               if isinstance(record, dict) and isinstance(record.get("id"), int)]
    if not records:
        pytest.skip("测试账号暂无画像解读历史，无法获取动态解读 ID")
    record_id = records[0]["id"]
    case_id = "PORTRAIT-DETAIL"
    detail = _raw_get(
        auth_client, f"/api/v1/health/portrait/interpretations/{record_id}",
        case_id,
    )
    assert isinstance(detail, dict), (
        f"{case_id} 响应应为对象，实际={type(detail).__name__}"
    )
    assert not {"code", "message", "data"}.issubset(detail), (
        f"{case_id} OpenAPI 定义原生 HealthInterpretationDetailResponse，"
        "实际返回了 Result 包装对象"
    )
    # 详情 schema 没有 required，也没有 id 字段；仅校验实际出现的契约字段。
    for field, expected_type in (
        ("status", int), ("gradeTextList", list), ("healthSummary", str),
        ("content", dict), ("createTime", str), ("abnormalMetricGroups", list),
    ):
        if field in detail:
            assert isinstance(detail[field], expected_type), (
                f"{case_id} {field} 类型异常：预期={expected_type.__name__}，"
                f"实际={type(detail[field]).__name__}"
            )


@pytest.mark.portrait
@pytest.mark.external
def test_portrait_data(auth_client):
    case_id = "PORTRAIT-DATA"
    data = _raw_get(auth_client, "/api/v1/health/portrait/data", case_id)
    assert isinstance(data, list), (
        f"{case_id} 响应应为数组，实际={type(data).__name__}"
    )
    for group in data:
        assert isinstance(group, dict) and isinstance(group.get("type"), int), (
            f"{case_id} 指标分组缺少整数 type"
        )
        assert group.get("isAbnormal") in (0, 1), (
            f"{case_id} isAbnormal 应为 0/1，实际={group.get('isAbnormal')!r}"
        )


@pytest.mark.portrait
def test_portrait_requires_auth(client):
    assert_rejected(client.get("/api/v1/health/portrait"),
                    "PORTRAIT-UNAUTHORIZED", expected_status=401)


@pytest.mark.portrait
@pytest.mark.external
def test_generate_portrait_interpretation():
    pytest.skip("生成健康解读调用心泰 AI，返回内容与额度不稳定且会写入记录")
