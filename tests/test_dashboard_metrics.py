"""P0 home and health metric read APIs from the current OpenAPI contract."""

from datetime import date, timedelta

import pytest

from common.assertions import assert_api_response, assert_rejected, safe_response_text


METRICS = ("heart_rate", "spo2", "bp", "tw")


def _dates():
    end = date.today()
    return {"startDate": (end - timedelta(days=7)).isoformat(),
            "endDate": end.isoformat()}


def _assert_metric(item, metric_type, case_id):
    assert isinstance(item, dict), f"{case_id} 指标条目应为对象，实际={type(item).__name__}"
    assert isinstance(item.get("id"), int), (
        f"{case_id} 指标缺少整数 id，条目字段={list(item)}"
    )
    assert item.get("metricType") == metric_type, (
        f"{case_id} 指标类型异常：预期={metric_type}，实际={item.get('metricType')}"
    )
    assert isinstance(item.get("metricValue"), (int, float)), (
        f"{case_id} metricValue 应为数值，实际={item.get('metricValue')!r}"
    )
    assert isinstance(item.get("recordTime"), str), (
        f"{case_id} recordTime 应为 ISO 日期时间文本，实际={item.get('recordTime')!r}"
    )


@pytest.mark.dashboard
@pytest.mark.smoke
@pytest.mark.parametrize("visible", (0, 1), ids=("hidden", "visible"))
def test_homepage_cards(auth_client, visible):
    case_id = f"DASH-CARDS-{visible}"
    response = auth_client.get("/api/v1/health/homepage/cards",
                               params={"visible": visible})
    assert response.status_code == 200, (
        f"{case_id} HTTP状态异常：预期=200，实际={response.status_code}，"
        f"响应={safe_response_text(response)}"
    )
    cards = response.json()  # This endpoint returns a raw array, not Result.
    assert isinstance(cards, list), (
        f"{case_id} 响应应为卡片数组，实际={type(cards).__name__}，"
        f"顶层字段={list(cards) if isinstance(cards, dict) else '不适用'}"
    )
    for card in cards:
        assert isinstance(card, dict) and isinstance(card.get("cardType"), str), (
            f"{case_id} 卡片缺少 cardType，条目字段={list(card) if isinstance(card, dict) else type(card).__name__}"
        )
        assert isinstance(card.get("orderNum"), int), (
            f"{case_id} 卡片 orderNum 应为整数，实际={type(card.get('orderNum')).__name__}"
        )


@pytest.mark.dashboard
def test_homepage_cards_requires_visible(auth_client):
    assert_rejected(auth_client.get("/api/v1/health/homepage/cards"),
                    "DASH-CARDS-MISSING-VISIBLE")


@pytest.mark.health
@pytest.mark.smoke
@pytest.mark.parametrize("metric_type", METRICS)
def test_latest_metric(auth_client, metric_type):
    case_id = f"METRIC-LATEST-{metric_type}"
    data = assert_api_response(
        auth_client.get("/api/v1/health/metrics/latest",
                        params={"metricType": metric_type, "limit": 10}),
        case_id,
    )
    # ResultListHealthMetricResponse documents null when there is no data.
    assert data is None or isinstance(data, list), (
        f"{case_id} data 应为数组或无数据时的 null，实际={type(data).__name__}"
    )
    for item in data or []:
        _assert_metric(item, metric_type, case_id)


@pytest.mark.health
@pytest.mark.parametrize("metric_type", METRICS)
def test_metric_history(auth_client, metric_type):
    case_id = f"METRIC-HISTORY-{metric_type}"
    data = assert_api_response(
        auth_client.get("/api/v1/health/metrics/history",
                        params={"metricType": metric_type, "page": 1,
                                "size": 10, **_dates()}),
        case_id, data_type=dict,
        required_fields=("list", "total", "pageNum", "pageSize", "pages"),
    )
    assert isinstance(data["list"], list), (
        f"{case_id} list 应为数组，实际={type(data['list']).__name__}"
    )
    assert all(isinstance(data[key], int) for key in
               ("total", "pageNum", "pageSize", "pages")), (
        f"{case_id} 分页字段应为整数，类型="
        f"{ {key: type(data[key]).__name__ for key in ('total', 'pageNum', 'pageSize', 'pages')} }"
    )
    for item in data["list"]:
        _assert_metric(item, metric_type, case_id)


@pytest.mark.health
@pytest.mark.parametrize("metric_type", METRICS)
def test_metric_summary(auth_client, metric_type):
    case_id = f"METRIC-SUMMARY-{metric_type}"
    data = assert_api_response(
        auth_client.get("/api/v1/health/metrics/summary",
                        params={"metricType": metric_type, **_dates()}),
        case_id, data_type=dict,
        required_fields=("metricType", "sampleCount"),
    )
    assert data["metricType"] == metric_type, (
        f"{case_id} 汇总类型异常：预期={metric_type}，实际={data['metricType']}"
    )
    assert isinstance(data["sampleCount"], int) and data["sampleCount"] >= 0, (
        f"{case_id} sampleCount 应为非负整数：{data['sampleCount']!r}"
    )


@pytest.mark.health
@pytest.mark.parametrize("params", ({}, {"metricType": "heart_rate", "limit": 0},
                                    {"metricType": "heart_rate", "limit": 101}),
                         ids=("missing-type", "limit-below-1", "limit-above-100"))
def test_latest_metric_invalid_query(auth_client, params):
    assert_rejected(auth_client.get("/api/v1/health/metrics/latest", params=params),
                    "METRIC-LATEST-INVALID")


@pytest.mark.health
def test_latest_metric_requires_auth(client):
    assert_rejected(client.get("/api/v1/health/metrics/latest",
                               params={"metricType": "heart_rate"}),
                    "METRIC-LATEST-UNAUTHORIZED", expected_status=401)


@pytest.mark.dashboard
@pytest.mark.external
@pytest.mark.parametrize("path", (
    "/api/v1/health/homepage/message-box",
    "/api/v1/health/homepage/health-box",
    "/api/v1/health/homepage/summary",
))
def test_external_homepage_risk_queries(path):
    pytest.skip(f"{path} 的风险信息由心泰实时提供；无可控第三方数据与状态")
