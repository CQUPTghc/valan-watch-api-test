"""Shared API clients. Authentication is performed once per pytest session."""

import logging

import pytest

from common.api_client import ApiClient
from common.assertions import assert_api_response
from config.settings import BASE_URL, VALAN_PASSWORD, VALAN_PHONE


LOGGER = logging.getLogger("valan.tests")


def pytest_runtest_setup(item):
    LOGGER.info("Case %s", item.nodeid)


@pytest.fixture(scope="session")
def client():
    if not BASE_URL:
        pytest.skip("未配置 BASE_URL；请设置 .env")
    instance = ApiClient(BASE_URL)
    yield instance
    instance.session.close()


@pytest.fixture(scope="session")
def auth_client():
    if not all((BASE_URL, VALAN_PHONE, VALAN_PASSWORD)):
        pytest.skip("缺少 BASE_URL / VALAN_PHONE / VALAN_PASSWORD 配置")
    instance = ApiClient(BASE_URL)
    try:
        response = instance.post(
            "/api/v1/auth/login/password",
            json={"phone": VALAN_PHONE, "password": VALAN_PASSWORD},
        )
        data = assert_api_response(
            response, "AUTH-FIXTURE", data_type=dict,
            required_fields=("accessToken",),
        )
        token = data["accessToken"]
        assert isinstance(token, str) and token, (
            "AUTH-FIXTURE 登录成功但 accessToken 为空"
        )
        instance.set_token(token)
        yield instance
    finally:
        instance.session.close()
