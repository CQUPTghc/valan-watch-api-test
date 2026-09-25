import os
import requests

from dotenv import load_dotenv
from locust import (
    HttpUser,
    task,
    constant_pacing,
    events,
)


load_dotenv()

BASE_URL = os.getenv("BASE_URL")
PHONE = os.getenv("VALAN_PHONE")
PASSWORD = os.getenv("VALAN_PASSWORD")

SHARED_TOKEN = None


@events.test_start.add_listener
def login_before_test(environment, **kwargs):
    """
    整个压测开始前只登录一次。
    避免同一账号被多个虚拟用户反复登录，
    导致旧 Token 失效。
    """
    global SHARED_TOKEN

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/password",
        json={
            "phone": PHONE,
            "password": PASSWORD
        },
        timeout=15
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"压测前登录失败，HTTP={response.status_code}"
        )

    body = response.json()

    if body.get("code") != 200:
        raise RuntimeError(
            f"压测前登录业务失败：{body}"
        )

    SHARED_TOKEN = body["data"]["accessToken"]

    print("压测账号登录成功，已获取共享 Token")


class ValanUser(HttpUser):
    host = BASE_URL

    # 每个用户大约每秒执行一轮任务
    wait_time = constant_pacing(1)

    def on_start(self):
        self.client.headers.update({
            "Authorization": f"Bearer {SHARED_TOKEN}"
        })

    def checked_get(self, path, name, params=None):
        with self.client.get(
            path,
            params=params,
            name=name,
            catch_response=True
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"HTTP={response.status_code}"
                )
                return

            try:
                body = response.json()
            except Exception:
                response.failure("响应不是 JSON")
                return

            if isinstance(body, dict):
                code = body.get("code")

                if code is not None and code != 200:
                    response.failure(
                        f"业务code={code}, "
                        f"message={body.get('message')}"
                    )

    @task(3)
    def current_user(self):
        self.checked_get(
            "/api/v1/auth/user/info",
            "01 当前用户信息"
        )

    @task(3)
    def health_profile(self):
        self.checked_get(
            "/api/v1/health/profile",
            "02 健康档案"
        )

    @task(2)
    def current_device(self):
        self.checked_get(
            "/api/v1/device/current",
            "03 当前设备"
        )

    @task(2)
    def family_members(self):
        self.checked_get(
            "/api/v1/family/members",
            "04 家庭成员列表"
        )

