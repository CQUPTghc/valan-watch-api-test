"""Assertions with concise, redacted failure details for HTML reports."""

import os
import re


_SENSITIVE_KEY = re.compile(
    r'(?i)(["\']?(?:accessToken|refreshToken|password|authorization|token)'
    r'["\']?\s*[:=]\s*["\']?)[^"\'\s,}]+')
_PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_IMEI = re.compile(r"(?<!\d)\d{15}(?!\d)")
_BEARER = re.compile(r"(?i)Bearer\s+[^\s,}\"']+")


def redact_text(value):
    """Keep diagnostic text while removing common credentials and phone numbers."""
    result = str(value)
    for key in ("VALAN_PASSWORD", "VALAN_PHONE", "VALAN_NONEXISTENT_PHONE"):
        secret = os.getenv(key)
        if secret:
            result = result.replace(secret, "<redacted>")
    result = _SENSITIVE_KEY.sub(r"\1<redacted>", result)
    result = _BEARER.sub("Bearer <redacted>", result)
    result = _PHONE.sub("<phone>", result)
    return _IMEI.sub("<imei>", result)


def safe_response_text(response, limit=600):
    text = redact_text(response.text)
    return text[:limit] + ("..." if len(text) > limit else "")


def _body(response, case_id):
    try:
        body = response.json()
    except ValueError as exc:
        raise AssertionError(
            f"{case_id} 响应不是 JSON：HTTP={response.status_code}，"
            f"响应={safe_response_text(response)}"
        ) from exc
    assert isinstance(body, dict), (
        f"{case_id} 响应顶层应为对象，实际={type(body).__name__}，"
        f"响应={safe_response_text(response)}"
    )
    return body


def assert_api_response(
    response, case_id, expected_status=200, expected_code=200,
    data_type=None, required_fields=(),
):
    """Assert a documented Result envelope and optional data contract."""
    assert response.status_code == expected_status, (
        f"{case_id} HTTP状态异常：预期={expected_status}，"
        f"实际={response.status_code}，响应={safe_response_text(response)}"
    )
    body = _body(response, case_id)
    assert body.get("code") == expected_code, (
        f"{case_id} 业务code异常：预期={expected_code}，"
        f"实际={body.get('code')}，响应={safe_response_text(response)}"
    )
    assert "data" in body, (
        f"{case_id} 响应缺少 data 字段：{safe_response_text(response)}"
    )
    data = body["data"]
    if data_type is not None:
        assert isinstance(data, data_type), (
            f"{case_id} data 类型异常：预期={data_type}，"
            f"实际={type(data).__name__}，响应={safe_response_text(response)}"
        )
    for field in required_fields:
        assert isinstance(data, dict) and field in data, (
            f"{case_id} data 缺少字段 {field}：{safe_response_text(response)}"
        )
    return data


def assert_rejected(response, case_id, expected_status=400, expected_code=None):
    """Assert a validation/auth error; assert an exact business code if documented.

    Several endpoints use specific business codes such as 40101 under HTTP 401.
    Their OpenAPI response schema does not promise that code equals HTTP status.
    """
    assert response.status_code == expected_status, (
        f"{case_id} 拒绝请求的HTTP状态异常：预期={expected_status}，"
        f"实际={response.status_code}，响应={safe_response_text(response)}"
    )
    body = _body(response, case_id)
    code = body.get("code")
    if expected_code is None:
        assert isinstance(code, int) and str(code).startswith("4"), (
            f"{case_id} 拒绝请求时应返回 4xx 系列业务code，"
            f"实际={code!r}，响应={safe_response_text(response)}"
        )
    else:
        assert code == expected_code, (
            f"{case_id} 拒绝请求的业务code异常：预期={expected_code}，"
            f"实际={code}，响应={safe_response_text(response)}"
        )
    return body
