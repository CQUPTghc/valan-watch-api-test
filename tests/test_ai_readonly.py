"""P1 AI session metadata and consent reads without generating AI content."""

import pytest

from common.assertions import assert_api_response, assert_rejected


def _sessions(auth_client):
    return assert_api_response(
        auth_client.get("/api/v1/ai/sessions", params={"page": 1, "size": 10}),
        "AI-SESSION-LIST", data_type=dict,
        required_fields=("list", "total", "pageNum", "pageSize", "pages"),
    )


@pytest.mark.ai
@pytest.mark.smoke
def test_ai_session_list(auth_client):
    data = _sessions(auth_client)
    assert isinstance(data["list"], list), "AI-SESSION-LIST list 应为数组"
    assert all(isinstance(data[key], int) and data[key] >= 0
               for key in ("total", "pageNum", "pageSize", "pages")), (
        "AI-SESSION-LIST 分页字段应为非负整数，类型="
        f"{ {key: type(data[key]).__name__ for key in ('total', 'pageNum', 'pageSize', 'pages')} }"
    )
    for session in data["list"]:
        assert isinstance(session, dict) and isinstance(session.get("sessionId"), str), (
            "AI-SESSION-LIST 会话缺少 sessionId"
        )
        assert isinstance(session.get("messageCount"), int), (
            "AI-SESSION-LIST messageCount 应为整数"
        )


@pytest.mark.ai
def test_ai_session_messages_when_available(auth_client):
    sessions = _sessions(auth_client)["list"]
    if not sessions:
        pytest.skip("测试账号暂无 AI 会话，无法获取动态 sessionId")
    session_id = sessions[0]["sessionId"]
    case_id = "AI-SESSION-MESSAGES"
    data = assert_api_response(
        auth_client.get(f"/api/v1/ai/sessions/{session_id}/messages",
                        params={"page": 1, "size": 10}),
        case_id, data_type=dict,
        required_fields=("list", "total", "pageNum", "pageSize", "pages"),
    )
    assert isinstance(data["list"], list), f"{case_id} list 应为数组"
    for message in data["list"]:
        assert isinstance(message, dict) and message.get("role") in (
            "user", "assistant", "system"), (
            f"{case_id} 消息 role 异常：{message.get('role') if isinstance(message, dict) else type(message).__name__}"
        )
        assert isinstance(message.get("content"), str), (
            f"{case_id} content 应为文本"
        )


@pytest.mark.ai
def test_ai_quick_prompts(auth_client):
    case_id = "AI-QUICK-PROMPTS"
    data = assert_api_response(auth_client.get("/api/v1/ai/quick-prompts"), case_id)
    # ResultListQuickPromptResponse permits null for no configured prompts.
    assert data is None or isinstance(data, list), (
        f"{case_id} data 应为数组或 null，实际={type(data).__name__}"
    )
    for prompt in data or []:
        assert isinstance(prompt, dict), f"{case_id} 快捷提问应为对象"
        assert isinstance(prompt.get("promptText"), str), (
            f"{case_id} 缺少 promptText 文本"
        )


@pytest.mark.ai
def test_ai_consent_state(auth_client):
    case_id = "AI-CONSENT-STATE"
    data = assert_api_response(
        auth_client.get("/api/v1/ai/consent"), case_id,
        data_type=dict, required_fields=("consents",),
    )
    assert isinstance(data["consents"], list), (
        f"{case_id} consents 应为数组：{type(data['consents']).__name__}"
    )
    for consent in data["consents"]:
        assert isinstance(consent, dict) and isinstance(consent.get("active"), bool), (
            f"{case_id} 授权记录缺少 active 布尔状态"
        )
        assert isinstance(consent.get("dataTypes"), list), (
            f"{case_id} 授权记录 dataTypes 应为数组"
        )


@pytest.mark.ai
@pytest.mark.parametrize("params", ({"page": 0}, {"size": 0}, {"size": 101}),
                         ids=("page-below-1", "size-below-1", "size-above-100"))
def test_ai_session_invalid_pagination(auth_client, params):
    assert_rejected(auth_client.get("/api/v1/ai/sessions", params=params),
                    "AI-SESSION-INVALID-PAGINATION")


@pytest.mark.ai
def test_ai_session_list_requires_auth(client):
    assert_rejected(client.get("/api/v1/ai/sessions"),
                    "AI-SESSION-UNAUTHORIZED", expected_status=401)


@pytest.mark.ai
@pytest.mark.external
def test_ai_send_stream():
    pytest.skip("AI SSE 内容和扣费依赖外部模型；本套件不生成不可控对话")
