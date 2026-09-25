"""认证接口回归。Token 只保存在内存中，不进入断言或日志。"""

import pytest

from common.api_client import ApiClient
from common.assertions import assert_api_response, assert_rejected
from config.settings import BASE_URL, VALAN_NONEXISTENT_PHONE, VALAN_PASSWORD, VALAN_PHONE


LOGIN_PATH = "/api/v1/auth/login/password"
USER_PATH = "/api/v1/auth/user/info"
REFRESH_PATH = "/api/v1/auth/token/refresh"


def _login(client, case_id):
    response = client.post(LOGIN_PATH, json={"phone": VALAN_PHONE, "password": VALAN_PASSWORD})
    assert_api_response(response, case_id, data_type=dict)
    data = response.json()["data"]
    for name in ("accessToken", "refreshToken"):
        assert isinstance(data.get(name), str) and data[name], (
            f"{case_id} 登录响应缺少有效的 {name}；"
            f"HTTP={response.status_code}，code={response.json().get('code')}"
        )
    return data


def _restore_shared_auth(client, auth_client, case_id):
    """独立登录可能使此前的 Access Token 失效，重建共享会话。"""
    renewed = _login(client, f"{case_id}-RESTORE")
    auth_client.set_token(renewed["accessToken"])


@pytest.mark.auth
@pytest.mark.smoke
def test_password_login_success(client, auth_client):
    """AUTH-001：密码登录返回可用 Token 和用户信息。"""
    try:
        data = _login(client, "AUTH-001")
        assert isinstance(data.get("expiresIn"), int) and data["expiresIn"] > 0, (
            "AUTH-001 expiresIn 应为正整数"
        )
        assert isinstance(data.get("user"), dict), "AUTH-001 登录响应缺少 user 对象"
        assert isinstance(data["user"].get("id"), int), "AUTH-001 user.id 类型错误"
    finally:
        _restore_shared_auth(client, auth_client, "AUTH-001")


@pytest.mark.auth
@pytest.mark.smoke
def test_get_current_user(auth_client):
    """AUTH-002：使用有效 Access Token 获取当前用户。"""
    response = auth_client.get(USER_PATH)
    assert_api_response(response, "AUTH-002", data_type=dict)
    user = response.json()["data"]
    assert isinstance(user.get("id"), int), "AUTH-002 缺少整数型用户 id"
    assert isinstance(user.get("memberId"), str), "AUTH-002 memberId 类型错误"
    assert isinstance(user.get("roles"), list), "AUTH-002 roles 应为列表"


@pytest.mark.auth
@pytest.mark.parametrize(
    "case_id, authorization",
    [("AUTH-003", None), ("AUTH-INVALID-TOKEN", "Bearer invalid-access-token")],
    ids=["AUTH-003-no-token", "AUTH-INVALID-TOKEN"],
)
def test_get_current_user_rejects_unauthorized(client, case_id, authorization):
    """无 Token 或无效 Token 不得读取用户信息。"""
    headers = {"Authorization": authorization} if authorization else {}
    isolated = ApiClient(BASE_URL)
    try:
        response = isolated.get(USER_PATH, headers=headers)
    finally:
        isolated.session.close()
    body = response.json()
    assert body.get("code") == 401, (
        f"{case_id} 未授权请求的业务code应为401，实际={body.get('code')}"
    )
    assert body.get("data") is None, f"{case_id} 未授权请求返回了用户数据"
    assert_rejected(response, case_id, expected_status=401, expected_code=401)


@pytest.mark.auth
@pytest.mark.parametrize(
    "case_id",
    ["AUTH-005", "AUTH-006", "AUTH-007", "AUTH-008", "AUTH-MISSING-PHONE", "AUTH-EMPTY-PHONE"],
    ids=[
        "AUTH-005-wrong-password", "AUTH-006-user-not-exist",
        "AUTH-007-invalid-phone", "AUTH-008-missing-password",
        "AUTH-MISSING-PHONE", "AUTH-EMPTY-PHONE",
    ],
)
def test_password_login_rejects_invalid_input(client, case_id):
    """已执行的手工案例及请求必填字段校验。"""
    cases = {
        "AUTH-005": ({"phone": VALAN_PHONE, "password": "WrongPassword123!"}, "密码错误"),
        "AUTH-006": ({"phone": VALAN_NONEXISTENT_PHONE, "password": "WrongPassword123!"}, "用户不存在"),
        "AUTH-007": ({"phone": "12345", "password": "WrongPassword123!"}, "手机号格式不正确"),
        "AUTH-008": ({"phone": VALAN_PHONE}, "密码不能为空"),
        "AUTH-MISSING-PHONE": ({"password": "WrongPassword123!"}, None),
        "AUTH-EMPTY-PHONE": ({"phone": "", "password": "WrongPassword123!"}, None),
    }
    request_body, expected_message = cases[case_id]
    if case_id == "AUTH-006" and not VALAN_NONEXISTENT_PHONE:
        pytest.skip("需在 .env 配置 VALAN_NONEXISTENT_PHONE")
    response = client.post(LOGIN_PATH, json=request_body)
    assert_rejected(response, case_id, expected_status=400)
    body = response.json()
    if expected_message is not None:
        assert body.get("message") == expected_message, (
            f"{case_id} 错误提示不符：预期={expected_message!r}，"
            f"实际={body.get('message')!r}"
        )
    assert body.get("data") is None, f"{case_id} 登录失败却返回了 data"


@pytest.mark.auth
def test_refresh_token_rotation(client, auth_client):
    """AUTH-REFRESH-001/002：刷新令牌轮换，新令牌可用，旧令牌失效。"""
    try:
        credentials = _login(client, "AUTH-REFRESH-SETUP")
        old_refresh = credentials["refreshToken"]
        response = client.post(REFRESH_PATH, json={"refreshToken": old_refresh})
        assert_api_response(response, "AUTH-REFRESH-001", data_type=dict)
        refreshed = response.json()["data"]
        new_access = refreshed.get("accessToken")
        new_refresh = refreshed.get("refreshToken")
        # 无论是否返回新的 Refresh Token，都重放旧值；失败报告要能显示安全影响。
        replay_response = client.post(REFRESH_PATH, json={"refreshToken": old_refresh})
        try:
            replay_code = replay_response.json().get("code")
        except (ValueError, AttributeError):
            replay_code = "non-json"
        assert isinstance(new_refresh, str) and new_refresh and new_refresh != old_refresh, (
            "AUTH-REFRESH-001 refreshToken 未按最新接口文档轮换；"
            f"旧 Token 重放结果：HTTP={replay_response.status_code}，code={replay_code}"
        )
        assert_rejected(
            replay_response, "AUTH-REFRESH-REPLAY", expected_status=401, expected_code=40102
        )
        assert isinstance(new_access, str) and new_access, "AUTH-REFRESH-001 未签发新 accessToken"

        probe = ApiClient(BASE_URL)
        try:
            probe.set_token(new_access)
            user_response = probe.get(USER_PATH)
            assert_api_response(user_response, "AUTH-REFRESH-002", data_type=dict)
            assert isinstance(user_response.json()["data"].get("id"), int), (
                "AUTH-REFRESH-002 新 Access Token 未返回有效用户 id"
            )
        finally:
            probe.session.close()
    finally:
        _restore_shared_auth(client, auth_client, "AUTH-REFRESH-001")


@pytest.mark.auth
@pytest.mark.parametrize(
    "case_id, payload, expected_status",
    [
        ("AUTH-REFRESH-MISSING", {}, 400),
        ("AUTH-REFRESH-INVALID", {"refreshToken": "invalid-refresh-token"}, 401),
    ],
    ids=["missing-refresh-token", "invalid-refresh-token"],
)
def test_refresh_token_rejects_invalid_input(client, case_id, payload, expected_status):
    response = client.post(REFRESH_PATH, json=payload)
    expected_code = 40102 if case_id == "AUTH-REFRESH-INVALID" else expected_status
    assert_rejected(
        response, case_id, expected_status=expected_status, expected_code=expected_code
    )
    assert response.json().get("data") is None, f"{case_id} 无效请求返回了 Token 数据"


@pytest.mark.auth
def test_logout_revokes_token(client, auth_client):
    """AUTH-004/BUG-AUTH-001：独立登录测试登出，并恢复共享 fixture 的会话。"""
    temporary = None
    try:
        credentials = _login(client, "AUTH-004-SETUP")
        temporary = ApiClient(BASE_URL)
        temporary.set_token(credentials["accessToken"])
        response = temporary.post("/api/v1/auth/logout")
        assert_api_response(response, "AUTH-004")
        probe = temporary.get(USER_PATH)
        body = probe.json()
        assert body.get("code") == 401, (
            f"AUTH-004 登出后的 Token 未返回拒绝业务码，实际={body.get('code')}"
        )
        assert body.get("data") is None, "AUTH-004 登出后的 Token 仍能读取用户数据"
        assert_rejected(probe, "AUTH-004-REVOKED", expected_status=401, expected_code=401)
    finally:
        if temporary is not None:
            temporary.session.close()
        # 后端可能按用户撤销会话；确保 session 级 fixture 可供后续模块使用。
        _restore_shared_auth(client, auth_client, "AUTH-004")


@pytest.mark.auth
@pytest.mark.external
def test_wechat_login_requires_external_service():
    pytest.skip("微信授权依赖真实微信会话")


@pytest.mark.auth
@pytest.mark.external
@pytest.mark.parametrize("operation", ["sms/send", "login/sms", "password/reset"])
def test_sms_auth_requires_external_service(operation):
    pytest.skip(f"{operation} 依赖真实短信服务与可控验证码")


@pytest.mark.auth
@pytest.mark.hardware
def test_biometric_login_requires_hardware():
    pytest.skip("生物识别登录需要设备与真实生物凭据")


@pytest.mark.auth
@pytest.mark.manual
def test_registration_requires_disposable_account():
    pytest.skip("注册会永久创建账号；需提供可清理的专用测试数据")


@pytest.mark.auth
@pytest.mark.manual
def test_password_change_requires_isolated_account():
    pytest.skip("虽有第二测试账号，但改密缺少已验证的原密码恢复与会话清理流程")
