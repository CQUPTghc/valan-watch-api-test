# V1 验收发现与契约待确认项

依据：根目录最新 OpenAPI、当前 pytest 断言与测试环境执行记录。2026-09-25 全量和 HTML 复跑均收集 188 条 case，结果为 147 PASS、10 FAIL、0 XFAIL、31 SKIP。以下保留的 FAIL 反映可复现的接口行为或前置依赖失败；未将 HTTP 200 自动视为业务成功，也未把实际返回形态直接当作最终契约。文档不记录账号、密码或令牌原值。逐例状态以 `reports/report.html` 为准。

## 已复现的后端行为与 OpenAPI 冲突

### AUTH-REFRESH-001：旧 Refresh Token 可重复使用

- **接口：** `POST /api/v1/auth/token/refresh`。
- **依据：** OpenAPI 描述“使用当前有效 Refresh Token 原子轮换 Access Token 和 Refresh Token”，同一个旧 Refresh Token 只能成功一次；旧令牌失效时业务码为 `40102`。
- **复现：** 独立登录取得令牌 → 用旧 Refresh Token 首次刷新 → 再用同一个旧值刷新。测试结束后重新登录，恢复共享测试会话。
- **实测：** 首次刷新后未观察到新的 Refresh Token；旧值第二次提交仍返回 HTTP 200、业务 `code=200`。用例不输出令牌内容。
- **影响：** 被复用或泄露的旧令牌仍可换取会话，破坏轮换的单次使用保证。
- **处理：** 保留 `test_refresh_token_rotation` 的 FAIL 和“新旧值必须不同、旧值重放必须失败”的断言。请后端核对令牌签发及原子失效实现；修复后再运行回归。当前未把此新问题整体标成 XFAIL。

## HTTP Transport Status 与 OpenAPI 不一致

### AUTH-003 / AUTH-INVALID-TOKEN / AUTH-004-REVOKED

- **接口：** `GET /api/v1/auth/user/info`，分别使用无 Token、无效 Token、登出后旧 Access Token。
- **OpenAPI：** 未认证响应为 HTTP 401 Unauthorized。
- **实测：** 三种情况均返回 HTTP 200，响应体 `code=401`、`message=未登录`、`data=null`。测试先核对业务拒绝与 `data=null`，随后在 HTTP 401 契约检查上失败。
- **影响：** 依赖 HTTP 状态判断认证失败的客户端、网关或监控会把该响应视为成功。现有证据表明业务层已拒绝访问，**不能据此声称未授权用户读到了用户资料**。
- **处理：** 保留 3 条 FAIL；请接口负责人确认项目是否正式采用“HTTP 200 + body.code 表示所有业务错误”的统一规则。若规则被正式确认，应先修订 OpenAPI，再按修订后的契约调整测试；在此之前严格要求 HTTP 401。

## 成功响应结构与 OpenAPI 不一致

### DASH-CARDS-0 / DASH-CARDS-1：首页卡片

- **接口：** `GET /api/v1/health/homepage/cards?visible=0/1`。
- **OpenAPI：** HTTP 200 返回裸卡片 `array`。
- **实测：** HTTP 200 返回 `{code, message, data}` Result 包装对象，卡片数组位于 `data`。
- **影响：** 按 OpenAPI 生成或实现的客户端会按顶层数组解析，无法直接消费当前响应。
- **处理：** 保留 2 条 FAIL；请后端与文档负责人确定最终响应结构。测试没有自动取 `response.json()["data"]` 来掩盖差异。

### PORTRAIT-PAGE：首页健康画像

- **接口：** `GET /api/v1/health/portrait`。
- **OpenAPI：** HTTP 200 返回原生 `HealthPortraitPageResponse` 对象，其属性包括 `metricGroups`、`sourceStatus`，schema 未声明这些属性为 `required`。
- **实测：** HTTP 200 顶层出现 `{code, message, data}` Result 包装。
- **处理：** 保留 1 条响应结构 FAIL；测试已修正为“出现字段时验证类型”，不再强制要求可选的 `metricGroups` 存在，但仍拒绝未声明的 Result 包装。

### PORTRAIT-HISTORY / PORTRAIT-DATA：画像列表

- **接口：** `GET /api/v1/health/portrait/interpretations` 与 `GET /api/v1/health/portrait/data`。
- **OpenAPI：** 两个接口的 HTTP 200 都返回裸 `array`。
- **实测：** 两个接口均返回顶层 `dict`，符合 Result 包装形态，而不是顶层数组。
- **处理：** 各保留 1 条 FAIL；等待后端与文档负责人确认最终契约，不将数组自动从 `data` 解包作为通过条件。

### PORTRAIT-DETAIL：受历史列表前置失败阻塞

- **接口：** `GET /api/v1/health/portrait/interpretations/{id}`。
- **当前结果：** 详情用例先调用历史列表获取动态 ID；由于该列表返回 `dict`，用例在列表契约检查处 FAIL，**本轮没有发出详情 GET**。因此这 1 条 FAIL 是前置依赖失败，不是详情响应已被证实不合约。
- **处理：** 保留前置断言；待历史列表结构确认并恢复后，再执行详情接口验证。详情测试已按最新 `HealthInterpretationDetailResponse` 校正：schema 无 `id` 属性，字段也未列为 `required`，故只校验实际出现的声明字段类型。

## 测试实现问题及已修正事项

- 画像页旧断言把未列入 `required` 的 `metricGroups` 当作必需字段；已按最新 schema 修正，同时保留顶层响应形态检查。
- 画像详情旧断言检查了 schema 中不存在的 `id`；已改为核对详情 schema 声明的可选字段类型。当前前置列表失败仍会保留为 FAIL。
- 登出用例的独立登录与临时客户端现在均在 `try/finally` 覆盖范围内，结束时关闭临时连接并重新登录恢复共享 fixture 的 Token。刷新测试的临时客户端也会关闭。
- 健康档案未授权用例先核对 `data=null`，再严格检查文档要求的 HTTP 401；未把未注明的具体业务码 `401` 强加为成功条件。
- 第二测试账号的家庭成员只读查找已执行，核对 `registered is True`，由原先的 SKIP 转为 PASS；关系写入仍因缺少安全回滚与审计清理契约而 SKIP。
- 修改类用例若原字段为 `null` 且无法构造可靠恢复值，会明确 SKIP。纯占位用例直接调用带具体原因的 `pytest.skip`，不再出现无断言请求或空 `pass` 伪测试。
- 通知等失败信息只保留必要的状态、字段或类型，避免把完整业务对象写入日志和 HTML 报告。

## 已修复的既有边界缺陷

人工台账曾记录 `height=50`、`weight=300` 返回 HTTP 500。最近环境运行中 `HP-HEIGHT-50` 和 `HP-WEIGHT-300` 均通过合法值写入、读回与恢复检查，正常显示 PASS。两例保留 `known_bug` 标记，但仅在明确重现“HTTP 500 且数据未改变”时条件式 XFAIL；其他新失败仍是 FAIL。真实硬件的 `BUG-CFG-001` 仍需设备环境人工复核，未计作本次新缺陷。
