"""Android App 版本检查；用例来源：台账 APPVER-001～005。"""

import os

import pytest

from common.assertions import assert_api_response, assert_rejected


pytestmark = pytest.mark.app_version
PATH = "/api/v1/app/version/check"
DECISIONS = {"NO_UPDATE", "OPTIONAL_UPDATE", "FORCE_UPDATE", "NO_AVAILABLE_VERSION"}


@pytest.mark.smoke
def test_android_version_check_without_login(client):
    """APPVER-001：公开接口返回有定义的升级决策，兼容环境日后发布新版本。"""
    channel = os.getenv("VALAN_APP_VERSION_CHANNEL", "ANDROID")
    build = os.getenv("VALAN_APP_CURRENT_BUILD", "1")
    response = client.get(PATH, params={"channel": channel, "currentBuild": build})
    assert_api_response(response, "APPVER-001")
    data = response.json().get("data")
    assert isinstance(data, dict), f"APPVER-001 data 应为对象，实际={type(data).__name__}"
    decision = data.get("decision")
    assert decision in DECISIONS, f"APPVER-001 升级决策非法：{decision!r}"
    if decision in {"OPTIONAL_UPDATE", "FORCE_UPDATE"}:
        assert isinstance(data.get("buildNumber"), int), (
            f"APPVER-001 {decision} 缺少整数构建号，实际={type(data.get('buildNumber')).__name__}"
        )
        assert isinstance(data.get("versionName"), str) and data["versionName"], (
            f"APPVER-001 {decision} 缺少版本名称"
        )
        assert isinstance(data.get("apkUrl"), str) and data["apkUrl"], (
            f"APPVER-001 {decision} 缺少 APK 地址"
        )
        assert data.get("channel") == "ANDROID", (
            f"APPVER-001 可更新版本渠道异常，实际={data.get('channel')!r}"
        )
    if decision == "NO_AVAILABLE_VERSION":
        assert data.get("versionId") is None and data.get("apkUrl") is None, (
            f"APPVER-001 无可用版本时不应返回下载目标，"
            f"versionId类型={type(data.get('versionId')).__name__}，"
            f"apkUrl类型={type(data.get('apkUrl')).__name__}"
        )


@pytest.mark.parametrize(
    "case_id, params",
    [
        ("APPVER-002", {"currentBuild": 1}),
        ("APPVER-003", {"channel": "ANDROID"}),
        ("APPVER-004", {"channel": "ANDROID", "currentBuild": "abc"}),
        ("APPVER-005", {"channel": "IOS", "currentBuild": 1}),
    ],
    ids=["missing-channel", "missing-build", "invalid-build-type", "unsupported-channel"],
)
def test_android_version_check_invalid_query(client, case_id, params):
    response = client.get(PATH, params=params)
    assert_rejected(response, case_id, expected_status=400)
