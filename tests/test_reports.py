"""P0 report lists and P1 third-party report read contracts."""

from datetime import date

import pytest

from common.assertions import assert_api_response


REPORT_LIST_CASES = (
    ("daily", lambda today: {"month": today.strftime("%Y-%m")}),
    ("weekly", lambda today: {"year": str(today.year)}),
    ("monthly", lambda today: {"year": str(today.year)}),
)


@pytest.mark.reports
@pytest.mark.smoke
@pytest.mark.parametrize("kind,query", REPORT_LIST_CASES,
                         ids=("daily", "weekly", "monthly"))
def test_health_report_list(auth_client, kind, query):
    case_id = f"REPORT-LIST-{kind}"
    data = assert_api_response(
        auth_client.get(f"/api/v1/reports/{kind}", params=query(date.today())),
        case_id,
    )
    # ResultListHealthReportResponse explicitly permits null for no data.
    assert data is None or isinstance(data, list), (
        f"{case_id} data 应为数组或无数据时的 null，实际={type(data).__name__}"
    )
    for report in data or []:
        assert isinstance(report, dict), (
            f"{case_id} 报告条目应为对象，实际={type(report).__name__}"
        )
        assert isinstance(report.get("id"), int), (
            f"{case_id} 报告缺少整数 id，字段={list(report)}"
        )
        assert report.get("reportType") == kind, (
            f"{case_id} 报告类型异常：预期={kind}，"
            f"实际={report.get('reportType')}"
        )
        assert isinstance(report.get("reportDate"), str), (
            f"{case_id} reportDate 应为日期文本，实际={type(report.get('reportDate')).__name__}"
        )


@pytest.mark.reports
def test_latest_daily_report(auth_client):
    case_id = "REPORT-DAILY-LATEST"
    data = assert_api_response(
        auth_client.get("/api/v1/reports/daily/latest"), case_id,
    )
    if data is None:
        pytest.skip(f"{case_id} 测试账号近三日无日报，无法验证摘要字段")
    assert isinstance(data, dict), (
        f"{case_id} data 应为对象，实际={type(data).__name__}"
    )
    assert isinstance(data.get("reportDate"), str), (
        f"{case_id} reportDate 应为日期文本，实际={type(data.get('reportDate')).__name__}"
    )
    if data.get("dataCompleteness") is not None:
        assert isinstance(data["dataCompleteness"], int) and 0 <= data["dataCompleteness"] <= 100, (
            f"{case_id} dataCompleteness 应在 0-100：{data['dataCompleteness']!r}"
        )


@pytest.mark.reports
def test_latest_daily_sync_status(auth_client):
    case_id = "REPORT-DAILY-SYNC"
    data = assert_api_response(
        auth_client.get("/api/v1/reports/daily/latest/sync-status"),
        case_id, data_type=dict, required_fields=("status", "completed", "retryable"),
    )
    expected_states = {"WAITING_IDENTITY", "PROFILE_REQUIRED", "SYNCING",
                       "READY", "NO_DATA", "FAILED"}
    assert data["status"] in expected_states, (
        f"{case_id} status 不在契约枚举中：{data['status']!r}"
    )
    assert isinstance(data["completed"], bool) and isinstance(data["retryable"], bool), (
        f"{case_id} completed/retryable 应为布尔值，实际类型="
        f"{type(data['completed']).__name__}/{type(data['retryable']).__name__}"
    )


def _third_party_page(auth_client, report_type=None):
    params = {"page": 1, "size": 10}
    if report_type:
        params["reportType"] = report_type
    return assert_api_response(
        auth_client.get("/api/v1/reports/third-party", params=params),
        f"REPORT-THIRD-PARTY-{report_type or 'ALL'}", data_type=dict,
        required_fields=("list", "total", "pageNum", "pageSize", "pages"),
    )


@pytest.mark.reports
@pytest.mark.parametrize("report_type", (None, "AIECG", "YTJ1012"),
                         ids=("all", "ecg", "vital-signs"))
def test_third_party_report_list(auth_client, report_type):
    case_id = f"REPORT-THIRD-PARTY-{report_type or 'ALL'}"
    data = _third_party_page(auth_client, report_type)
    assert isinstance(data["list"], list), f"{case_id} list 应为数组"
    assert all(isinstance(data[key], int) for key in
               ("total", "pageNum", "pageSize", "pages")), (
        f"{case_id} 分页字段类型异常："
        f"{ {key: type(data[key]).__name__ for key in ('total', 'pageNum', 'pageSize', 'pages')} }"
    )
    for report in data["list"]:
        assert isinstance(report, dict) and isinstance(report.get("reportId"), int), (
            f"{case_id} 报告缺少整数 reportId，"
            f"条目类型={type(report).__name__}"
        )
        assert report.get("reportType") in ("AIECG", "YTJ1012"), (
            f"{case_id} reportType 不在契约枚举中：{report.get('reportType')!r}"
        )
        if report_type:
            assert report["reportType"] == report_type, (
                f"{case_id} 筛选未生效：实际={report['reportType']}"
            )


@pytest.mark.reports
def test_third_party_report_detail_when_available(auth_client):
    reports = _third_party_page(auth_client)["list"]
    if not reports:
        pytest.skip("测试账号没有第三方报告，无法从列表获取动态 reportId")
    report_id = reports[0]["reportId"]
    case_id = "REPORT-THIRD-PARTY-DETAIL"
    data = assert_api_response(
        auth_client.get(f"/api/v1/reports/third-party/{report_id}"),
        case_id, data_type=dict, required_fields=("reportId", "reportType"),
    )
    assert data["reportId"] == report_id, (
        f"{case_id} 详情 ID 与列表不一致：列表={report_id}，详情={data['reportId']}"
    )
    assert data["reportType"] == reports[0]["reportType"], (
        f"{case_id} 详情类型与列表不一致：列表={reports[0]['reportType']}，"
        f"详情={data['reportType']}"
    )


@pytest.mark.reports
@pytest.mark.external
def test_report_h5_access():
    pytest.skip("心泰/彩之物 H5 地址依赖第三方报告服务及真实报告数据")


@pytest.mark.reports
@pytest.mark.external
def test_third_party_media_access():
    pytest.skip("报告介质访问地址由乐普第三方签发，测试账号无可控介质")
