"""P1 message center read checks; read-state mutations are intentionally excluded."""

import pytest

from common.assertions import assert_api_response, assert_rejected


CATEGORIES = ("ALERT", "HEALTH", "DEVICE", "FAMILY", "SYSTEM")


@pytest.mark.notifications
@pytest.mark.parametrize("category", (None, *CATEGORIES),
                         ids=("all", "alert", "health", "device", "family", "system"))
def test_notification_list(auth_client, category):
    case_id = f"NOTIFICATION-LIST-{category or 'ALL'}"
    params = {"page": 1, "size": 10}
    if category:
        params["category"] = category
    data = assert_api_response(
        auth_client.get("/api/v1/notifications", params=params),
        case_id, data_type=dict,
        required_fields=("list", "total", "page", "size", "unreadCounts"),
    )
    assert isinstance(data["list"], list), f"{case_id} list 应为数组"
    assert all(isinstance(data[key], int) and data[key] >= 0
               for key in ("total", "page", "size")), (
        f"{case_id} 分页字段应为非负整数，类型="
        f"{ {key: type(data[key]).__name__ for key in ('total', 'page', 'size')} }"
    )
    assert isinstance(data["unreadCounts"], dict), (
        f"{case_id} unreadCounts 应为对象，实际={type(data['unreadCounts']).__name__}"
    )
    for name, count in data["unreadCounts"].items():
        assert name in CATEGORIES and isinstance(count, int) and count >= 0, (
            f"{case_id} 未读分类或数量异常：{name}={count!r}"
        )
    for notice in data["list"]:
        assert isinstance(notice, dict) and isinstance(notice.get("id"), int), (
            f"{case_id} 消息缺少整数 id"
        )
        assert notice.get("category") in CATEGORIES, (
            f"{case_id} 消息分类不在契约枚举中：{notice.get('category')!r}"
        )
        assert isinstance(notice.get("read"), bool), (
            f"{case_id} 消息 read 应为布尔值"
        )
        if category:
            assert notice["category"] == category, (
                f"{case_id} 分类筛选未生效：实际={notice['category']}"
            )


@pytest.mark.notifications
@pytest.mark.smoke
def test_unread_notification_count(auth_client):
    case_id = "NOTIFICATION-UNREAD-COUNT"
    data = assert_api_response(
        auth_client.get("/api/v1/notifications/unread-count"),
        case_id, data_type=dict, required_fields=("unreadCount",),
    )
    assert isinstance(data["unreadCount"], int) and data["unreadCount"] >= 0, (
        f"{case_id} unreadCount 应为非负整数：{data['unreadCount']!r}"
    )


@pytest.mark.notifications
@pytest.mark.parametrize("params", (
    {"page": 0}, {"size": 0}, {"size": 101}, {"category": "UNKNOWN"},
), ids=("page-below-1", "size-below-1", "size-above-100", "unknown-category"))
def test_notification_invalid_query(auth_client, params):
    assert_rejected(auth_client.get("/api/v1/notifications", params=params),
                    "NOTIFICATION-INVALID-QUERY")


@pytest.mark.notifications
def test_notification_list_requires_auth(client):
    assert_rejected(client.get("/api/v1/notifications"),
                    "NOTIFICATION-UNAUTHORIZED", expected_status=401)


@pytest.mark.notifications
@pytest.mark.manual
def test_mark_notification_read():
    pytest.skip("标记消息已读不可恢复；缺少专用可清理消息，不修改共享账号未读状态")
