"""家庭成员读取与权限参数校验；关系变更需要隔离账号才可执行。"""

import os

import pytest

from common.assertions import assert_api_response, assert_rejected


pytestmark = pytest.mark.family


def _list_data(response, case_id):
    assert_api_response(response, case_id)
    data = response.json().get("data")
    assert data is None or isinstance(data, list), (
        f"{case_id} data 应为列表或 null，实际={type(data).__name__}"
    )
    for index, item in enumerate(data or []):
        assert isinstance(item, dict), f"{case_id} 第{index}条记录应为对象"
    return data or []


@pytest.mark.smoke
def test_family_members(auth_client):
    """FAM-001：家庭成员列表允许为空。"""
    members = _list_data(auth_client.get("/api/v1/family/members"), "FAM-001")
    for index, member in enumerate(members):
        assert isinstance(member.get("memberId"), str) and member["memberId"], (
            f"FAM-001 第{index}名家人缺少 memberId"
        )
        assert isinstance(member.get("relationId"), int), (
            f"FAM-001 第{index}名家人缺少 relationId"
        )
        assert member.get("accessStatus") in {"NONE", "PENDING", "AUTHORIZED"}, (
            f"FAM-001 第{index}名家人授权状态非法：{member.get('accessStatus')!r}"
        )


@pytest.mark.parametrize("case_id,direction", [("FAM-002", "RECEIVED"), ("FAM-003", "SENT")])
def test_family_binding_requests(auth_client, case_id, direction):
    """旧版兼容绑定申请列表，供既有客户端读取。"""
    requests = _list_data(
        auth_client.get("/api/v1/family/requests", params={"direction": direction}),
        case_id,
    )
    for index, item in enumerate(requests):
        assert isinstance(item.get("relationId"), int), (
            f"{case_id} 第{index}条绑定申请缺少 relationId"
        )
        assert item.get("status") in {"PENDING", "ACTIVE", "REJECTED", "EXPIRED", "UNBOUND"}, (
            f"{case_id} 第{index}条绑定申请状态非法：{item.get('status')!r}"
        )


@pytest.mark.parametrize(
    "case_id,params",
    [
        ("FAM-004", {"direction": "INVALID"}),
        ("FAM-006", {"direction": "RECEIVED", "status": "INVALID"}),
        ("FAM-REQUEST-MISSING-DIRECTION", {}),
    ],
)
def test_family_binding_requests_invalid_query(auth_client, case_id, params):
    assert_rejected(
        auth_client.get("/api/v1/family/requests", params=params),
        case_id,
        expected_status=400,
    )


@pytest.mark.parametrize("case_id,direction", [("FAM-ACCESS-001", "RECEIVED"), ("FAM-ACCESS-002", "SENT")])
def test_family_access_requests(auth_client, case_id, direction):
    """新版单向家人读取授权申请列表。"""
    items = _list_data(
        auth_client.get("/api/v1/family/access-requests", params={"direction": direction}),
        case_id,
    )
    for index, item in enumerate(items):
        assert isinstance(item.get("relationId"), int), (
            f"{case_id} 第{index}条授权申请缺少 relationId"
        )
        assert item.get("requestStatus") in {
            "PENDING", "ACCEPTED", "REJECTED", "EXPIRED", "CANCELLED", None
        }, f"{case_id} 第{index}条授权申请状态非法：{item.get('requestStatus')!r}"


@pytest.mark.parametrize(
    "case_id,params",
    [
        ("FAM-ACCESS-INVALID-DIRECTION", {"direction": "INVALID"}),
        ("FAM-ACCESS-INVALID-STATUS", {"direction": "RECEIVED", "status": "INVALID"}),
        ("FAM-ACCESS-MISSING-DIRECTION", {}),
    ],
)
def test_family_access_requests_invalid_query(auth_client, case_id, params):
    assert_rejected(
        auth_client.get("/api/v1/family/access-requests", params=params),
        case_id,
        expected_status=400,
    )


@pytest.mark.parametrize(
    "case_id,direction",
    [("FAM-GRANTS-001", "CAN_VIEW"), ("FAM-GRANTS-002", "VIEWING_ME")],
)
def test_family_access_grants(auth_client, case_id, direction):
    """按当前登录人的视角读取生效的单向授权。"""
    items = _list_data(
        auth_client.get("/api/v1/family/accesses", params={"direction": direction}),
        case_id,
    )
    for index, item in enumerate(items):
        assert isinstance(item.get("relationId"), int), (
            f"{case_id} 第{index}条授权缺少 relationId"
        )
        assert item.get("accessStatus") == "AUTHORIZED", (
            f"{case_id} 第{index}条生效授权状态异常：{item.get('accessStatus')!r}"
        )


@pytest.mark.parametrize(
    "case_id,params",
    [
        ("FAM-GRANTS-INVALID-DIRECTION", {"direction": "INVALID"}),
        ("FAM-GRANTS-MISSING-DIRECTION", {}),
    ],
)
def test_family_access_grants_invalid_query(auth_client, case_id, params):
    assert_rejected(
        auth_client.get("/api/v1/family/accesses", params=params),
        case_id,
        expected_status=400,
    )


def test_family_member_detail(auth_client):
    """FAM-011：成员 ID 和关系 ID 从成员列表动态取得。"""
    members = _list_data(auth_client.get("/api/v1/family/members"), "FAM-011-prerequisite")
    if not members:
        pytest.skip("当前账号无家庭成员，无法运行成员详情正向查询")
    member = members[0]
    member_id = member.get("memberId")
    assert isinstance(member_id, str) and member_id, "FAM-011 前置成员缺少 memberId"
    response = auth_client.get(f"/api/v1/family/members/{member_id}")
    assert_api_response(response, "FAM-011")
    detail = response.json().get("data")
    assert isinstance(detail, dict), f"FAM-011 data 应为对象，实际={type(detail).__name__}"
    assert detail.get("memberId") == member_id, (
        f"FAM-011 返回成员不匹配，预期={member_id}，实际={detail.get('memberId')}"
    )
    assert detail.get("relationId") == member.get("relationId"), (
        f"FAM-011 关系 ID 不匹配，预期={member.get('relationId')}，"
        f"实际={detail.get('relationId')}"
    )


def test_family_access_grant_detail(auth_client):
    """按动态 relationId 查询当前可查看的授权详情。"""
    items = _list_data(
        auth_client.get("/api/v1/family/accesses", params={"direction": "CAN_VIEW"}),
        "FAM-GRANT-DETAIL-prerequisite",
    )
    if not items:
        pytest.skip("当前账号无生效的 CAN_VIEW 单向家人授权")
    relation_id = items[0].get("relationId")
    assert isinstance(relation_id, int), "授权列表缺少 relationId"
    response = auth_client.get(
        f"/api/v1/family/accesses/{relation_id}",
        params={"direction": "CAN_VIEW"},
    )
    assert_api_response(response, "FAM-GRANT-DETAIL")
    detail = response.json().get("data")
    assert isinstance(detail, dict), (
        f"FAM-GRANT-DETAIL data 应为对象，实际={type(detail).__name__}"
    )
    assert detail.get("relationId") == relation_id, (
        f"FAM-GRANT-DETAIL 关系 ID 不匹配，预期={relation_id}，"
        f"实际={detail.get('relationId')}"
    )
    assert detail.get("accessStatus") == "AUTHORIZED", (
        f"FAM-GRANT-DETAIL 授权状态异常：{detail.get('accessStatus')!r}"
    )


def test_family_lookup_requires_phone(auth_client):
    assert_rejected(
        auth_client.get("/api/v1/family/members/lookup"),
        "FAM-LOOKUP-MISSING-PHONE",
        expected_status=400,
    )


def test_family_lookup_configured_account(auth_client):
    """手机号仅由 .env 提供，测试报告不输出原值。"""
    phone = os.getenv("VALAN_FAMILY_TEST_PHONE")
    if not phone:
        pytest.skip("需在 .env 配置 VALAN_FAMILY_TEST_PHONE 才能查询专用家人测试账号")
    response = auth_client.get("/api/v1/family/members/lookup", params={"phone": phone})
    assert_api_response(response, "FAM-LOOKUP-REGISTERED")
    data = response.json().get("data")
    assert isinstance(data, dict), (
        f"FAM-LOOKUP-REGISTERED data 应为对象，实际={type(data).__name__}"
    )
    assert isinstance(data.get("registered"), bool), (
        "FAM-LOOKUP-REGISTERED 缺少 registered 布尔字段"
    )
    assert data["registered"] is True, (
        "FAM-LOOKUP-REGISTERED 已配置的独立测试账号未被识别为已注册"
    )


@pytest.mark.parametrize(
    "case_id,path,params",
    [
        ("FAM-MEMBERS-UNAUTH", "/api/v1/family/members", None),
        ("FAM-REQUESTS-UNAUTH", "/api/v1/family/requests", {"direction": "RECEIVED"}),
        ("FAM-ACCESS-UNAUTH", "/api/v1/family/access-requests", {"direction": "RECEIVED"}),
        ("FAM-GRANTS-UNAUTH", "/api/v1/family/accesses", {"direction": "CAN_VIEW"}),
    ],
)
def test_family_data_requires_token(client, case_id, path, params):
    assert_rejected(client.get(path, params=params), case_id, expected_status=401)


def test_family_data_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/family/members",
        headers={"Authorization": "Bearer invalid-api-test-token"},
    )
    assert_rejected(response, "FAM-MEMBERS-INVALID-TOKEN", expected_status=401)


@pytest.mark.parametrize(
    "case_id,reason",
    [
        ("FAM-007~011", "第二测试账号已提供；邀请与接受会创建关系，当前缺少完整回滚与审计清理契约"),
        ("FAM-012~014", "跨成员指标、日报及 H5 需先建立可恢复授权关系及受控健康数据"),
        ("FAM-015~017", "解绑真实家庭关系不可自动恢复原授权状态"),
        ("FAM-ACCESS-REQUEST-WRITE", "第二测试账号已提供；授权申请仍缺完整关系回滚策略"),
        ("FAM-ACCESS-REVOKE", "撤销授权会影响真实家庭数据可见性，缺少可验证恢复流程"),
    ],
    ids=["invite-and-accept", "cross-member-data", "unbind", "access-request", "revoke"],
)
@pytest.mark.manual
@pytest.mark.destructive
def test_family_relationship_workflow_excluded(case_id, reason):
    pytest.skip(f"{case_id}：{reason}")
