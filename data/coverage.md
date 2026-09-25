# OpenAPI operation 覆盖矩阵（V1）

依据：根目录 `维朗斯健康智能体 - API接口文档.openapi.json`（2026-09-24 版本）、`tests/` 中现有 pytest、`V1_APP功能项分级清单-20260901.md` 和 P0/P1 原型。统计日期：2026-09-25。主 OpenAPI 是本表的完整分母，包含 P2 和暂未纳入本轮的接口。

## 统计口径

- 一个 operation = 一个 HTTP 方法 + OpenAPI 路径模板；动态 ID 归一到 `{deviceId}`、`{relationId}` 等模板。119 个 path 共 134 个 operation。
- `AUTO` 表示已编写能实际发请求并检查状态、业务码或响应结构的 pytest 用例；失败的契约断言仍计为 AUTO。`Cases` 是以该 operation 为主要检查目标的已收集用例数，不重复计算 fixture 和前置查询。部分正向用例因缺少动态数据会在运行时 SKIP。
- `SKIP-*` 与 `MANUAL` 是本台账明确排除的操作，不等于 pytest 报告的 SKIPPED 数；Reason 会说明是否已有 `pytest.skip` 占位。纯占位函数一律不算 AUTO。`NOT-COVERED` 是尚无断言也无已执行自动化的缺口。
- 绑定、解绑、换绑三个写操作目前仅有输入校验/不存在资源的负向自动化；真实设备的成功流程仍需人工硬件验证。

## 总览

| 指标 | 数量 |
| --- | ---: |
| OpenAPI path | 119 |
| OpenAPI operation | 134 |
| AUTO operation | 48 |
| SKIP-HARDWARE operation | 9 |
| SKIP-EXTERNAL operation | 22 |
| SKIP-DESTRUCTIVE operation | 22 |
| MANUAL operation | 1 |
| NOT-COVERED operation | 32 |
| 以 AUTO operation 为主要目标的已编写 pytest case | 162 |
| 当前收集的全部 pytest case（含 26 条明确调用 `pytest.skip` 的占位） | 188 |

已明确 SKIP/MANUAL 的 operation 合计 **54**；与 32 个 `NOT-COVERED` 分开统计。最近一次环境运行的 PASS/FAIL/XFAIL/SKIP 以 README 和 `reports/report.html` 为准，这些运行结果不是 operation 覆盖数。

## 模块分布

| Module | OpenAPI Ops | AUTO | SKIP/MANUAL | NOT-COVERED |
| --- | ---: | ---: | ---: | ---: |
| 第三方报告 | 3 | 2 | 1 | 0 |
| 会员服务 | 1 | 0 | 0 | 1 |
| 积分服务 | 3 | 0 | 1 | 2 |
| 家庭成员 | 10 | 5 | 5 | 0 |
| 家庭成员授权 | 3 | 2 | 1 | 0 |
| 健康报告 | 5 | 5 | 0 | 0 |
| 健康指标 | 4 | 3 | 0 | 1 |
| 紧急联系人 | 2 | 1 | 1 | 0 |
| 内容查询 | 1 | 0 | 0 | 1 |
| 认证管理 | 11 | 4 | 7 | 0 |
| 设备绑定 | 6 | 5 | 1 | 0 |
| 设备管理 | 2 | 2 | 0 | 0 |
| 首页仪表盘 | 5 | 1 | 4 | 0 |
| 文件上传 | 2 | 0 | 2 | 0 |
| 心泰设备管理 | 9 | 1 | 8 | 0 |
| 心泰AI能力 | 35 | 4 | 5 | 26 |
| 心泰H5代理 | 6 | 0 | 6 | 0 |
| 用户信息 | 7 | 6 | 1 | 0 |
| AI健康顾问 | 14 | 4 | 9 | 1 |
| App版本检查 | 1 | 1 | 0 | 0 |
| App消息中心 | 4 | 2 | 2 | 0 |

## 逐 operation 明细

| Module | Endpoint | Method | Automated | Cases | Status | Reason |
| --- | --- | --- | --- | ---: | --- | --- |
| AI健康顾问 | `/api/v1/ai/consent` | DELETE | NO | 0 | SKIP-DESTRUCTIVE | 撤回全部同意会改变用户合法授权状态；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/consent` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| AI健康顾问 | `/api/v1/ai/consent` | POST | NO | 0 | SKIP-DESTRUCTIVE | 授权留痕会写入真实同意记录；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/consent/{consentVersion}` | DELETE | NO | 0 | SKIP-DESTRUCTIVE | 撤回指定版本同意不可恢复审计轨迹；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/quick-prompts` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| AI健康顾问 | `/api/v1/ai/requests/{requestId}` | GET | NO | 0 | NOT-COVERED | 尚无可控异步 requestId，未编写状态断言 |
| AI健康顾问 | `/api/v1/ai/send` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；SSE、外部模型、费用及生成内容不可控 |
| AI健康顾问 | `/api/v1/ai/session` | POST | NO | 0 | SKIP-DESTRUCTIVE | 创建持久会话，尚无隔离及清理链路；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/sessions` | DELETE | NO | 0 | SKIP-DESTRUCTIVE | 清空历史会话不可恢复；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/sessions` | GET | YES | 5 | AUTO | 已编写请求与契约断言 |
| AI健康顾问 | `/api/v1/ai/sessions/{sessionId}` | DELETE | NO | 0 | SKIP-DESTRUCTIVE | 删除历史会话不可恢复；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/sessions/{sessionId}` | PATCH | NO | 0 | SKIP-DESTRUCTIVE | 重命名真实会话，尚无受控原值/恢复用例；无 pytest 用例 |
| AI健康顾问 | `/api/v1/ai/sessions/{sessionId}/messages` | GET | YES | 1 | AUTO | 有会话时动态取 ID；否则运行时跳过 |
| AI健康顾问 | `/api/v1/ai/sessions/batch-delete` | POST | NO | 0 | SKIP-DESTRUCTIVE | 批量删除真实会话不可恢复；无 pytest 用例 |
| App版本检查 | `/api/v1/app/version/check` | GET | YES | 5 | AUTO | 已编写请求与契约断言 |
| 认证管理 | `/api/v1/auth/login/biometric` | POST | NO | 0 | SKIP-HARDWARE | pytest skip 占位；需真实设备及生物凭据 |
| 认证管理 | `/api/v1/auth/login/password` | POST | YES | 7 | AUTO | 已编写请求与契约断言 |
| 认证管理 | `/api/v1/auth/login/sms` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；真实短信或微信服务 |
| 认证管理 | `/api/v1/auth/login/wechat` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；真实短信或微信服务 |
| 认证管理 | `/api/v1/auth/logout` | POST | YES | 1 | AUTO | 登出后旧令牌业务拒绝与 HTTP 契约 |
| 认证管理 | `/api/v1/auth/password/change` | PUT | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 占位；虽有第二测试账号，仍缺已验证的原密码恢复及会话清理流程 |
| 认证管理 | `/api/v1/auth/password/reset` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；真实短信或微信服务 |
| 认证管理 | `/api/v1/auth/register` | POST | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 占位；会永久建号，缺少可清理数据 |
| 认证管理 | `/api/v1/auth/sms/send` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；真实短信或微信服务 |
| 认证管理 | `/api/v1/auth/token/refresh` | POST | YES | 3 | AUTO | 轮换/重放及异常输入断言；当前轮换存在 FAIL |
| 认证管理 | `/api/v1/auth/user/info` | GET | YES | 3 | AUTO | 正常查询及未认证 HTTP 契约；当前未认证状态存在 FAIL |
| 内容查询 | `/api/v1/content/{contentKey}` | GET | NO | 0 | NOT-COVERED | 尚无经确认的稳定 contentKey 与响应断言 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/configuration/measurements/{metricType}` | PUT | NO | 0 | SKIP-HARDWARE | pytest skip 占位；真实设备下发及可恢复配置未就绪 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/configuration/sos-contacts` | PUT | NO | 0 | SKIP-HARDWARE | pytest skip 占位；真实设备下发及可恢复配置未就绪 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/detail` | GET | YES | 3 | AUTO | 正向依赖可用设备 ID；另有不存在/未认证断言 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/fences` | GET | NO | 0 | SKIP-HARDWARE | 电子围栏依赖真实设备位置及可控测试环境；无 pytest 用例 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/fences` | POST | NO | 0 | SKIP-HARDWARE | 围栏写入依赖真实设备和清理策略；无 pytest 用例 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/fences/{duid}` | DELETE | NO | 0 | SKIP-HARDWARE | 围栏删除依赖真实设备和重建恢复；无 pytest 用例 |
| 心泰设备管理 | `/api/v1/device/{deviceId}/fences/{duid}` | PUT | NO | 0 | SKIP-HARDWARE | 围栏更新依赖真实设备和原值恢复；无 pytest 用例 |
| 设备绑定 | `/api/v1/device/bind` | POST | YES | 6 | AUTO | 仅参数拒绝；真实绑定正向场景仍需硬件 |
| 设备绑定 | `/api/v1/device/current` | GET | YES | 3 | AUTO | 已编写请求与契约断言 |
| 设备绑定 | `/api/v1/device/history` | GET | YES | 3 | AUTO | 已编写请求与契约断言 |
| 设备绑定 | `/api/v1/device/history/{bindingId}/hide` | POST | NO | 0 | SKIP-DESTRUCTIVE | 隐藏历史设备记录不可从当前契约恢复；无 pytest 用例 |
| 设备绑定 | `/api/v1/device/replace` | POST | YES | 1 | AUTO | 仅缺失字段拒绝；真实换绑仍需硬件 |
| 设备绑定 | `/api/v1/device/unbind` | POST | YES | 3 | AUTO | 仅参数拒绝/不存在设备；真实解绑仍需硬件 |
| 设备管理 | `/api/v1/devices/{deviceId}` | GET | YES | 2 | AUTO | 正向依赖可用设备 ID；另有不存在设备断言 |
| 设备管理 | `/api/v1/devices/imei/{imei}` | GET | YES | 2 | AUTO | 正向依赖完整测试 IMEI；另有不存在设备断言 |
| 家庭成员 | `/api/v1/family/access-requests` | GET | YES | 6 | AUTO | 已编写请求与契约断言 |
| 家庭成员 | `/api/v1/family/access-requests/{accessRequestId}/decision` | POST | NO | 0 | SKIP-DESTRUCTIVE | 处理授权申请会改变真实关系状态；无独立 pytest 用例 |
| 家庭成员授权 | `/api/v1/family/accesses` | GET | YES | 5 | AUTO | 已编写请求与契约断言 |
| 家庭成员授权 | `/api/v1/family/accesses/{relationId}` | DELETE | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 分组占位；撤权影响家庭数据可见性 |
| 家庭成员授权 | `/api/v1/family/accesses/{relationId}` | GET | YES | 1 | AUTO | 有授权时通过列表动态取 ID；否则运行时跳过 |
| 家庭成员 | `/api/v1/family/members` | GET | YES | 3 | AUTO | 已编写请求与契约断言 |
| 家庭成员 | `/api/v1/family/members/{memberId}` | GET | YES | 1 | AUTO | 有成员时通过列表动态取 ID；否则运行时跳过 |
| 家庭成员 | `/api/v1/family/members/lookup` | GET | YES | 2 | AUTO | 缺失手机号拒绝及配置账号查询；正向依赖环境变量 |
| 家庭成员 | `/api/v1/family/relations/{relationId}/access-requests` | POST | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 分组占位；需双账号与关系清理策略 |
| 家庭成员 | `/api/v1/family/relations/{relationId}/unbind` | POST | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 分组占位；解绑后不能精确恢复原关系和授权 |
| 家庭成员 | `/api/v1/family/requests` | GET | YES | 6 | AUTO | 已编写请求与契约断言 |
| 家庭成员 | `/api/v1/family/requests` | POST | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 分组占位；邀请会创建真实家庭关系，需隔离双账号和清理 |
| 家庭成员 | `/api/v1/family/requests/{relationId}/decision` | POST | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 分组占位；接受/拒绝会改变真实关系状态 |
| 文件上传 | `/api/v1/files/{resourceType}/{resourceId}/download` | GET | NO | 0 | SKIP-EXTERNAL | 下载签名依赖已有第三方资源；无 pytest 用例 |
| 文件上传 | `/api/v1/files/upload` | POST | NO | 0 | SKIP-DESTRUCTIVE | 上传创建持久资源，缺少删除/恢复契约；无 pytest 用例 |
| 心泰H5代理 | `/api/v1/h5/diet-record` | GET | NO | 0 | SKIP-EXTERNAL | 心泰 H5 会话/跳转依赖外部服务；无 pytest 用例 |
| 心泰H5代理 | `/api/v1/h5/home` | GET | NO | 0 | SKIP-EXTERNAL | 心泰 H5 会话/跳转依赖外部服务；无 pytest 用例 |
| 心泰H5代理 | `/api/v1/h5/innovation-research` | GET | NO | 0 | SKIP-EXTERNAL | 心泰 H5 会话/跳转依赖外部服务；无 pytest 用例 |
| 心泰H5代理 | `/api/v1/h5/report` | GET | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；第三方 H5 地址及报告数据不可控 |
| 心泰H5代理 | `/api/v1/h5/tongue-face-diagnose` | GET | NO | 0 | SKIP-EXTERNAL | 心泰 H5 会话/跳转依赖外部服务；无 pytest 用例 |
| 心泰H5代理 | `/api/v1/h5/web-home` | GET | NO | 0 | SKIP-EXTERNAL | 心泰 H5 会话/跳转依赖外部服务；无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/calories` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/dates` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/foods/{foodId}` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/foods/custom` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/foods/library` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/foods/recognitions/by-image` | POST | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/foods/recognitions/by-name` | POST | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/meals` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/meals` | PUT | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/meals/{dietId}` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/meals/analyses` | POST | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes/{recipeId}` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes/{recipeId}` | PATCH | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes/by-date` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes/distributions` | POST | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/diet/recipes/executing` | GET | NO | 0 | NOT-COVERED | 膳食管理不在本次 P0/P1 范围，尚无 pytest 用例 |
| 首页仪表盘 | `/api/v1/health/homepage/cards` | GET | YES | 3 | AUTO | 裸数组契约；当前 Result 包装导致 2 例 FAIL |
| 首页仪表盘 | `/api/v1/health/homepage/cards/rearrangement` | POST | NO | 0 | SKIP-DESTRUCTIVE | 修改共享首页卡片排序/显隐，尚无安全读回恢复用例 |
| 首页仪表盘 | `/api/v1/health/homepage/health-box` | GET | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；心泰实时风险数据不可控 |
| 首页仪表盘 | `/api/v1/health/homepage/message-box` | GET | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；心泰实时风险数据不可控 |
| 首页仪表盘 | `/api/v1/health/homepage/summary` | GET | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；心泰实时风险数据不可控 |
| 健康指标 | `/api/v1/health/metrics/ecg/{metricId}` | GET | NO | 0 | NOT-COVERED | P0 ECG 详情尚未从列表构造有效 metricId；无 pytest 用例 |
| 健康指标 | `/api/v1/health/metrics/history` | GET | YES | 4 | AUTO | 已编写请求与契约断言 |
| 健康指标 | `/api/v1/health/metrics/latest` | GET | YES | 8 | AUTO | 已编写请求与契约断言 |
| 健康指标 | `/api/v1/health/metrics/summary` | GET | YES | 4 | AUTO | 已编写请求与契约断言 |
| 心泰AI能力 | `/api/v1/health/ocr/recognitions` | POST | NO | 0 | NOT-COVERED | OCR 当前归 P2；依赖受控图像和外部识别，尚无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/ocr/reports/{reportId}` | GET | NO | 0 | NOT-COVERED | OCR 当前归 P2；尚无可控 reportId 和断言 |
| 心泰AI能力 | `/api/v1/health/portrait` | GET | YES | 2 | AUTO | 页面结构断言；当前测试字段待按最新 schema 复核 |
| 心泰AI能力 | `/api/v1/health/portrait/abnormal-metrics` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/abnormal-metrics/calendar` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/ai/generations` | POST | NO | 0 | SKIP-EXTERNAL | 心泰 AI 生成结果及费用不可控；无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/portrait/ai/latest` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/carousel` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/data` | GET | YES | 1 | AUTO | 裸数组契约；当前包装响应导致 FAIL |
| 心泰AI能力 | `/api/v1/health/portrait/home` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations` | GET | YES | 1 | AUTO | 裸数组契约；当前包装响应导致 FAIL |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations` | POST | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；心泰 AI 生成并写入解读记录 |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations/{id}` | GET | YES | 1 | AUTO | 动态 ID 详情；当前历史列表契约失败阻断前置 |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations/{id}/text` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations/comparisons` | POST | NO | 0 | SKIP-EXTERNAL | 依赖真实解读数据与外部 AI；无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/portrait/interpretations/latest` | GET | NO | 0 | NOT-COVERED | 画像只读扩展接口尚未编写断言；需稳定账号数据或动态 ID |
| 用户信息 | `/api/v1/health/profile` | GET | YES | 3 | AUTO | 已编写请求与契约断言 |
| 用户信息 | `/api/v1/health/profile` | PUT | YES | 25 | AUTO | 合法/非法边界、GET 读回与 finally 恢复 |
| 心泰AI能力 | `/api/v1/health/tongue-diagnosis/reports/{reportId}` | GET | NO | 0 | SKIP-EXTERNAL | 需心泰舌面诊真实报告与动态 ID；无 pytest 用例 |
| 心泰AI能力 | `/api/v1/health/tongue-diagnosis/sessions` | POST | NO | 0 | SKIP-EXTERNAL | 需上传真实图像并调用心泰模型；无 pytest 用例 |
| 会员服务 | `/api/v1/membership` | GET | NO | 0 | NOT-COVERED | 会员中心当前归 P2，尚无 pytest 用例 |
| App消息中心 | `/api/v1/notifications` | GET | YES | 11 | AUTO | 已编写请求与契约断言 |
| App消息中心 | `/api/v1/notifications/{notificationId}/read` | PUT | NO | 0 | SKIP-DESTRUCTIVE | 单条已读状态不可恢复；无 pytest 用例 |
| App消息中心 | `/api/v1/notifications/read-all` | PUT | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 占位；已读状态不可恢复 |
| App消息中心 | `/api/v1/notifications/unread-count` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 积分服务 | `/api/v1/points` | GET | NO | 0 | NOT-COVERED | 积分中心当前归 P2，尚无 pytest 用例 |
| 积分服务 | `/api/v1/points/exchange/{itemId}` | POST | NO | 0 | MANUAL | OpenAPI 标注积分兑换已禁用且属 P2；重新启用前由业务人工确认 |
| 积分服务 | `/api/v1/points/transactions` | GET | NO | 0 | NOT-COVERED | 积分明细当前归 P2，尚无 pytest 用例 |
| 健康报告 | `/api/v1/reports/daily` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 健康报告 | `/api/v1/reports/daily/latest` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 健康报告 | `/api/v1/reports/daily/latest/sync-status` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 健康报告 | `/api/v1/reports/monthly` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 第三方报告 | `/api/v1/reports/third-party` | GET | YES | 3 | AUTO | 已编写请求与契约断言 |
| 第三方报告 | `/api/v1/reports/third-party/{reportId}` | GET | YES | 1 | AUTO | 有报告时动态取 ID；否则运行时跳过 |
| 第三方报告 | `/api/v1/reports/third-party/{reportId}/access` | GET | NO | 0 | SKIP-EXTERNAL | pytest skip 占位；报告介质签名需真实第三方资源 |
| 健康报告 | `/api/v1/reports/weekly` | GET | YES | 1 | AUTO | 已编写请求与契约断言 |
| 紧急联系人 | `/api/v1/user/emergency-contacts` | GET | YES | 2 | AUTO | 已编写请求与契约断言 |
| 紧急联系人 | `/api/v1/user/emergency-contacts` | PUT | NO | 0 | SKIP-DESTRUCTIVE | pytest skip 占位；GET 只返回脱敏手机号，无法精确恢复 replace |
| 用户信息 | `/api/v1/user/profile` | GET | YES | 2 | AUTO | 已编写请求与契约断言 |
| 用户信息 | `/api/v1/user/profile` | PUT | YES | 5 | AUTO | 有效昵称读回恢复及非法参数不污染 |
| 用户信息 | `/api/v1/user/settings` | GET | YES | 2 | AUTO | 已编写请求与契约断言 |
| 用户信息 | `/api/v1/user/settings` | PUT | YES | 4 | AUTO | 有效字号读回恢复及非法参数不污染 |
| 用户信息 | `/api/v1/user/xintai-identity/retry` | POST | NO | 0 | SKIP-EXTERNAL | 触发心泰身份同步，依赖第三方且无可恢复结果；无 pytest 用例 |
| 心泰设备管理 | `/api/v1/xintai/devices/bound` | GET | NO | 0 | SKIP-HARDWARE | 需真实心泰绑定设备与同步状态；无 pytest 用例 |
| 心泰设备管理 | `/api/v1/xintai/devices/info` | GET | NO | 0 | SKIP-HARDWARE | 需真实完整 IMEI 及厂家设备数据；无 pytest 用例 |

## 非 OpenAPI 的 P0/P1 待确认接口

这些需求不在 134 个 operation 分母中，不根据 UI 路径猜测后端接口，也不计为自动化覆盖：

- P0 手工健康指标录入：当前主 OpenAPI 未给出对应用户侧写入 operation（原台账 `GAP-MANUAL-001`）。
- P1 健康问卷提交和注册协议版本留痕：主 OpenAPI 未给出可执行契约（`GAP-QUESTIONNAIRE-001`、`GAP-AGREEMENT-001`）。
- 睡眠细分页 `/api/sleep/*` 仍为 PRD 拟议路径；运动主要由心泰 H5 承载。待文档负责人发布正式 operation 后再计入分母。
