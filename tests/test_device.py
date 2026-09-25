"""设备读取和本地参数校验；真实设备生命周期操作单独标记跳过。"""

import os
import re
import uuid

import pytest

from common.assertions import assert_api_response, assert_rejected


pytestmark = pytest.mark.device
CURRENT = "/api/v1/device/current"
HISTORY = "/api/v1/device/history"
# 人工台账 DEVQ-003/004 使用此不存在的测试标识；它不是实际设备 IMEI。
NONEXISTENT_DEVICE = "000000000000000"


@pytest.fixture(scope="module")
def bound_device(auth_client):
    response = auth_client.get(CURRENT)
    assert_api_response(response, "DEV-001-prerequisite")
    data = response.json().get("data")
    if data is None:
        pytest.skip("当前账号没有已绑定设备，设备详情正向场景缺少前置数据")
    assert isinstance(data, dict), f"DEV-001 data 应为设备对象，实际={type(data).__name__}"
    assert data.get("bindingStatus") == "ACTIVE", (
        f"DEV-001 当前设备绑定状态异常，实际={data.get('bindingStatus')!r}"
    )
    return data


@pytest.fixture(scope="module")
def device_imei(bound_device):
    imei = os.getenv("VALAN_TEST_DEVICE_IMEI") or bound_device.get("imei")
    if not isinstance(imei, str) or not re.fullmatch(r"\d{15}", imei):
        pytest.skip("当前设备接口仅返回脱敏 IMEI；需在 .env 配置 VALAN_TEST_DEVICE_IMEI")
    return imei


@pytest.fixture(scope="module")
def device_id(auth_client, bound_device):
    known_id = bound_device.get("deviceId") or os.getenv("VALAN_TEST_DEVICE_ID")
    if known_id:
        return str(known_id)
    imei = os.getenv("VALAN_TEST_DEVICE_IMEI") or bound_device.get("imei")
    if not isinstance(imei, str) or not re.fullmatch(r"\d{15}", imei):
        pytest.skip("当前设备未返回 deviceId/完整 IMEI；需配置 VALAN_TEST_DEVICE_ID 或 VALAN_TEST_DEVICE_IMEI")
    response = auth_client.get(f"/api/v1/devices/imei/{imei}")
    assert_api_response(response, "DEVQ-001-prerequisite")
    data = response.json().get("data")
    assert isinstance(data, dict), f"DEVQ-001 data 应为设备对象，实际={type(data).__name__}"
    value = data.get("deviceId")
    assert isinstance(value, str) and value, (
        f"DEVQ-001 未返回 deviceId，响应字段={list(data)}"
    )
    return value


@pytest.mark.smoke
def test_current_device(auth_client):
    """DEV-001：当前绑定摘要可读，未绑定时允许 data=null。"""
    response = auth_client.get(CURRENT)
    assert_api_response(response, "DEV-001")
    data = response.json().get("data")
    assert data is None or isinstance(data, dict), (
        f"DEV-001 data 类型错误：{type(data).__name__}"
    )
    if data is not None:
        assert data.get("bindingStatus") == "ACTIVE", (
            f"DEV-001 当前设备应为 ACTIVE，实际={data.get('bindingStatus')!r}"
        )
        assert isinstance(data.get("imei"), str) and data["imei"], (
            f"DEV-001 缺少设备标识，响应字段={list(data)}"
        )


def test_device_history(auth_client):
    """DEV-002：历史解绑记录不混入当前 ACTIVE 设备。"""
    response = auth_client.get(HISTORY)
    assert_api_response(response, "DEV-002")
    data = response.json().get("data")
    assert data is None or isinstance(data, list), (
        f"DEV-002 data 应为列表或 null，实际={type(data).__name__}"
    )
    for index, item in enumerate(data or []):
        assert isinstance(item, dict), f"DEV-002 第{index}条历史记录不是对象"
        assert item.get("bindingStatus") != "ACTIVE", (
            f"DEV-002 历史列表混入 ACTIVE 绑定，记录ID={item.get('id')}"
        )
        assert item.get("boundAt") and item.get("unboundAt"), (
            f"DEV-002 历史记录缺少绑定/解绑时间，记录ID={item.get('id')}"
        )


@pytest.mark.parametrize("case_id,path", [("DEV-003", CURRENT), ("DEV-004", HISTORY)])
def test_device_list_requires_token(client, case_id, path):
    assert_rejected(client.get(path), case_id, expected_status=401)


@pytest.mark.parametrize("case_id,path", [("DEV-TOKEN-001", CURRENT), ("DEV-TOKEN-002", HISTORY)])
def test_device_list_rejects_invalid_token(client, case_id, path):
    response = client.get(path, headers={"Authorization": "Bearer invalid-api-test-token"})
    assert_rejected(response, case_id, expected_status=401)


def test_lookup_device_by_imei(auth_client, device_imei):
    """DEVQ-001：使用测试环境设备 IMEI，检查查询结果的标识和数据类型。"""
    response = auth_client.get(f"/api/v1/devices/imei/{device_imei}")
    assert_api_response(response, "DEVQ-001")
    data = response.json().get("data")
    assert isinstance(data, dict), f"DEVQ-001 data 应为设备对象，实际={type(data).__name__}"
    assert isinstance(data.get("deviceId"), str) and data["deviceId"], (
        f"DEVQ-001 缺少 deviceId，响应字段={list(data)}"
    )
    assert isinstance(data.get("status"), int), (
        f"DEVQ-001 设备状态类型错误，实际={type(data.get('status')).__name__}"
    )


def test_lookup_device_by_id(auth_client, device_id):
    """DEVQ-002：deviceId 由当前设备查询得到，不写死。"""
    response = auth_client.get(f"/api/v1/devices/{device_id}")
    assert_api_response(response, "DEVQ-002")
    data = response.json().get("data")
    assert isinstance(data, dict), f"DEVQ-002 data 应为设备对象，实际={type(data).__name__}"
    assert str(data.get("deviceId")) == device_id, (
        f"DEVQ-002 查询设备ID与返回值不一致，预期={device_id}，实际={data.get('deviceId')}"
    )


@pytest.mark.parametrize(
    "case_id,path",
    [
        ("DEVQ-003", f"/api/v1/devices/imei/{NONEXISTENT_DEVICE}"),
        ("DEVQ-004", f"/api/v1/devices/{NONEXISTENT_DEVICE}"),
    ],
)
def test_lookup_nonexistent_device(auth_client, case_id, path):
    assert_rejected(auth_client.get(path), case_id, expected_status=400)


@pytest.mark.external
def test_device_detail(auth_client, device_id):
    """DETD-001：详情可能调用心泰实时设备服务。"""
    response = auth_client.get(f"/api/v1/device/{device_id}/detail")
    assert_api_response(response, "DETD-001")
    data = response.json().get("data")
    assert isinstance(data, dict), f"DETD-001 data 应为对象，实际={type(data).__name__}"
    assert isinstance(data.get("device"), dict), (
        f"DETD-001 缺少设备基本信息，响应字段={list(data)}"
    )
    assert str(data["device"].get("deviceId")) == device_id, (
        f"DETD-001 返回设备不匹配，预期={device_id}，实际={data['device'].get('deviceId')}"
    )
    for key in ("location", "configuration", "sync", "capabilities", "dataStatus"):
        assert key in data, f"DETD-001 缺少详情分区 {key}，响应字段={list(data)}"


def test_nonexistent_device_detail(auth_client):
    """DETD-002：不存在的设备不会泄露其他设备详情。"""
    path = f"/api/v1/device/{NONEXISTENT_DEVICE}/detail"
    assert_rejected(auth_client.get(path), "DETD-002", expected_status=404)


def test_device_detail_requires_token(client):
    """DETD-004：未登录不能读取设备位置和配置。"""
    path = f"/api/v1/device/{NONEXISTENT_DEVICE}/detail"
    assert_rejected(client.get(path), "DETD-004", expected_status=401)


@pytest.mark.parametrize(
    "case_id,payload",
    [
        ("BIND-001", {"operationId": "api-test-missing-imei"}),
        ("BIND-002", {"imei": NONEXISTENT_DEVICE}),
        ("BIND-003", {"imei": "12345678901234", "operationId": "api-test-short-imei"}),
        ("BIND-004", {"imei": "12345678901234A", "operationId": "api-test-letter-imei"}),
        ("BIND-007", {"imei": NONEXISTENT_DEVICE, "operationId": "x" * 65}),
        ("BIND-008", {"imei": NONEXISTENT_DEVICE, "operationId": ""}),
    ],
)
def test_bind_rejects_invalid_request(auth_client, case_id, payload):
    """输入校验在设备供应商调用前完成；所有 IMEI 均为无效测试标识。"""
    response = auth_client.post("/api/v1/device/bind", json=payload)
    assert_rejected(response, case_id, expected_status=400)


@pytest.mark.parametrize(
    "case_id,payload",
    [
        ("UNBIND-002", {"imei": NONEXISTENT_DEVICE}),
        ("UNBIND-003", {"operationId": "api-test-missing-imei"}),
    ],
)
def test_unbind_rejects_missing_fields(auth_client, case_id, payload):
    response = auth_client.post("/api/v1/device/unbind", json=payload)
    assert_rejected(response, case_id, expected_status=400)


def test_unbind_nonexistent_device(auth_client):
    """UNBIND-001：仅使用人工台账确认不存在的设备标识。"""
    response = auth_client.post(
        "/api/v1/device/unbind",
        json={"imei": NONEXISTENT_DEVICE, "operationId": f"api-test-{uuid.uuid4().hex}"},
    )
    assert_rejected(response, "UNBIND-001", expected_status=404)


def test_replace_rejects_missing_new_imei(auth_client):
    """REPLACE-002：缺少新设备标识时在参数校验层拒绝。"""
    response = auth_client.post(
        "/api/v1/device/replace",
        json={"oldImei": NONEXISTENT_DEVICE, "operationId": "api-test-missing-new-imei"},
    )
    assert_rejected(response, "REPLACE-002", expected_status=400)


@pytest.mark.parametrize(
    "case_id,reason",
    [
        ("BIND-POSITIVE", "绑定真实硬件会改变账号设备归属；缺少专用备用设备及可验证恢复流程"),
        ("UNBIND-POSITIVE", "解绑真实硬件会中断当前账号业务；缺少专用备用设备及可验证恢复流程"),
        ("REPLACE-POSITIVE", "换绑会改变两台设备关系；缺少专用备用设备及可验证恢复流程"),
        ("CFG-MEAS-001", "自动测量配置依赖真实硬件与心泰下发，BUG-CFG-001 仍待修复"),
        ("CFG-SOS-POSITIVE", "SOS 联系人可能触发真实紧急联系行为，缺少隔离硬件环境"),
    ],
    ids=["bind", "unbind", "replace", "measurement-config", "sos-contacts"],
)
@pytest.mark.hardware
@pytest.mark.external
@pytest.mark.manual
def test_device_hardware_workflow_excluded(case_id, reason):
    pytest.skip(f"{case_id}：{reason}")
