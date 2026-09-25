# Valan Watch 接口自动化测试

基于现有 `requests` 客户端、`.env` 和 session 登录 fixture 扩展的 pytest 集成测试。接口来源为根目录最新 OpenAPI、V1 APP 功能项分级清单、P0/P1 原型及人工测试台账。每条失败断言保留用例编号、期望/实际状态和脱敏响应；请求日志只记录方法、路径、HTTP 状态与失败摘要。

当前收集 188 条 pytest case；OpenAPI 共 119 个 path、134 个 HTTP 方法+路径 operation，其中 48 个 operation 编写了自动化断言。2026-09-25 全量与 HTML 报告复跑均为 **147 PASS、10 FAIL、0 XFAIL、31 SKIP**。FAIL 包含已复现的后端行为或接口契约差异，不表示 pytest 框架无法运行；**SKIP 不等于 PASS**，也不计作已自动化接口。覆盖和问题性质分别见 [覆盖清单](data/coverage.md) 与 [问题记录](data/findings.md)。

## 1. 安装依赖

Windows PowerShell，Python 3.14：

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果已有 `.venv` 的 Python 无法启动，先检查 Python 3.14 安装和当前终端的执行权限；确认虚拟环境损坏后再重新创建。项目源码不依赖 Codex 的本地运行时。

## 2. 配置 `.env`

```powershell
Copy-Item .env.example .env
```

填写隔离测试环境的 `BASE_URL`、`VALAN_PHONE`、`VALAN_PASSWORD`、`VALAN_NONEXISTENT_PHONE`。不要写入真实生产账号。设备正向查询可选填 `VALAN_TEST_DEVICE_IMEI`、`VALAN_TEST_DEVICE_ID`；家人账号只读查找可选填 `VALAN_FAMILY_TEST_PHONE`。版本检查可覆盖 `VALAN_APP_VERSION_CHANNEL` 与 `VALAN_APP_CURRENT_BUILD`。`.env` 和 `reports/` 已被 Git 忽略；不要将账号密码或完整 Token 粘贴到报告和提交记录。

## 3. 执行全部测试

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

首次执行建议先运行 `--collect-only -q` 核对收集情况。需要访问 `.env` 指向的 API；网络不通时连接错误不代表后端缺陷。测试默认串行运行，避免同一账号上的修改类测试相互覆盖。

## 4. 执行单模块

```powershell
.\.venv\Scripts\python.exe -m pytest -v tests\test_health_profile.py
.\.venv\Scripts\python.exe -m pytest -v -m family
```

## 5. 只跑 smoke

```powershell
.\.venv\Scripts\python.exe -m pytest -v -m smoke
```

## 6. 排除硬件和第三方接口

```powershell
.\.venv\Scripts\python.exe -m pytest -v -m "not hardware and not external"
```

`hardware`、`external`、`manual`、`destructive` 用例保留具体跳过原因。硬件绑定/配置、AI 实时生成、短信/微信、真实家庭关系写入需要可控环境和回滚流程。已有第二测试账号可用于只读查找；创建、撤销家庭关系仍因缺少完整恢复与审计清理契约而跳过。详见 [覆盖与人工测试说明](data/coverage.md)。

## 7. 生成 HTML 报告

PowerShell 续行符是反引号 `` ` ``，不是 `cmd.exe` 的 `^`：

```powershell
New-Item -ItemType Directory -Force reports | Out-Null
.\.venv\Scripts\python.exe -m pytest -v `
    --html=reports/report.html `
    --self-contained-html
```

执行结束后打开 `reports/report.html`。也可以把命令写成一行。报告会按 pytest 状态区分 PASSED、FAILED、XFAIL、SKIPPED。

## 8. 查看失败与已知缺陷

```powershell
.\.venv\Scripts\python.exe -m pytest -v -ra --tb=short
.\.venv\Scripts\python.exe -m pytest -v -m known_bug -rx
```

健康档案合法边界 `height=50`、`weight=300` 是此前已提交的缺陷；最近环境运行均已 PASS。仅当 HTTP 500 明确重现且档案未被污染时才记为 XFAIL，其他失败仍为 FAIL。`known_bug` marker 仅用于筛选，不会自动掩盖断言。当前 Refresh Token 轮换、鉴权 HTTP 状态、首页卡片与画像响应结构的 FAIL 保留，依据与影响见 [问题记录](data/findings.md)。

## 测试数据与恢复

可恢复修改用例先 GET 原值，PUT 后再 GET 核验，最后在 `finally` 中查询当前值；只有发生变化才 PUT 原值并再次 GET 核验。动态 Token、成员 ID、设备 ID 均从登录/查询响应或 `.env` 获取。原字段为 `null` 且无法恢复、缺少隔离硬件或缺少安全回滚路径时，用例给出明确 SKIP 原因。
