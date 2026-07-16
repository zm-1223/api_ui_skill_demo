# api_ui_skill_demo — Tigshop 电商自动化测试

基于 **ecommerce-cart-payment-tests** Skill，对接 [Tigshop 演示站](https://demo.tigshop.cn/)，采用 **API + UI(POM)** 双层结构。

## 目录结构

```
api_ui_skill_demo/
├── api/                 # 接口客户端与鉴权
│   ├── auth_helper.py
│   └── shop_api_client.py
├── config/              # 全局配置（读取 data/test_data.json）
│   └── settings.py
├── ui/                  # POM 页面对象（禁止 test 写 locator）
│   ├── base_page.py
│   ├── login_page.py
│   ├── product_page.py
│   ├── cart_page.py
│   ├── checkout_page.py
│   ├── payment_page.py
│   └── order_page.py
├── utils/               # 等待、弹窗、日志、Token 复用、浏览器工厂
│   ├── wait_helper.py
│   ├── popup_helper.py
│   ├── logger_helper.py
│   ├── token_store.py
│   └── browser_helper.py
├── tests/
│   ├── api/             # 24 条 API 用例
│   └── e2e/             # 15 条 UI 用例
├── data/
│   ├── test_data.json
│   └── prerequisites.md
├── reports/             # HTML 报告与截图
├── case.md              # 用例计划
├── pytest.ini
└── requirements.txt
```

## 环境

| 项 | 值 |
|----|-----|
| 站点 | https://demo.tigshop.cn/ |
| 账号 | `123123` / `123123` |
| 商品页 | `/item/SN0000548` |

## Token 复用（方案 B，推荐）

演示站登录可能触发**滑块验证码**，且直接调登录 API 可能返回 `code=1002`。因此默认**不在每条用例里重复登录**，而是会话级复用一次 `accessToken`。

### 一次性配置（任选其一）

| 方式 | 操作 |
|------|------|
| **本地文件** | 浏览器登录 [demo.tigshop.cn](https://demo.tigshop.cn) → F12 → Cookie → 复制 `accessToken` → 填入 `data/token.json` 的 `access_token` 或 `token` |
| **环境变量** | `set TIGSHOP_ACCESS_TOKEN=<你的token>`（PowerShell/CMD） |
| **UI 兜底** | 在 `data/test_data.json` 设置 `token_cache.allow_ui_login_fallback: true`（可能仍需手动过滑块） |

`data/token.json` 已加入 `.gitignore`，勿提交到仓库。

### 运行机制

```
pytest 启动
  → shared_access_token（session）
    → TokenStore：内存 → 环境变量 → token.json → API 校验(getCount)
  → API 用例：ShopApiClient(token=shared_access_token)
  → UI 用例：AuthHelper.inject_token_to_driver() 注入 Cookie，跳过登录页
```

仅 **AUTH-001/002** 等登录专项 UI 用例仍走 `LoginPage` 真实登录流程。

### Fixture 作用域（方案 3：少开浏览器）

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `shared_access_token` | session | 全套件共用一个 token |
| `driver` / `logged_in_driver` | **class** | 同一 TestClass 共用一个 Chrome（约 5 次/全量 UI） |
| `driver`（`test_auth.py`） | **function** | 登录用例需独立 session，覆盖 class 级 |
| `ui_browser` | **module** | 每个 API 测试文件共用一个 Chrome（约 3 次） |
| `ui_add_product_once` | function | 仅 API-CART-002 UI 加购验证 |
| `api_add_product_once` | function | 默认 API 加购前置（addToCart） |
| ChromeDriver 路径 | session | `utils/browser_helper.py` 缓存，避免重复 install |

**预期**：Chrome 冷启动从 ~34 次降至 ~10 次（2 auth + 3 UI class + 3 API module + 缓存 driver）。

## 测试报告（浏览器打开）

运行 `pytest` 后会生成两类 HTML：

| 报告 | 路径 | 说明 |
|------|------|------|
| **pytest-html** | `reports/report.html` | 单文件，双击即可打开，**无需 Allure CLI** |
| **Allure** | `reports/allure-report/index.html` | 需 Allure CLI 生成，图表更丰富 |

### 一键流程

```bash
pip install -r requirements.txt
# 先配置 token（见上文「Token 复用」）
pytest                              # 写入 allure-results + report.html；结束自动尝试生成 Allure HTML
python scripts/generate_allure_report.py   # 手动从 allure-results 生成 Allure HTML
```

### Allure CLI 安装（Windows）

```bash
scoop install allure
# 或下载 https://github.com/allure-framework/allure2/releases 解压并加入 PATH
```

### 浏览器打开方式

- 资源管理器双击 `reports/report.html`
- 或 `reports/allure-report/index.html`
- 地址栏：`file:///D:/github-code/api_ui_skill_demo/reports/report.html`

UI 失败截图会附加到 Allure 报告，并保存到 `reports/screenshots/`。

## 安装与运行

```bash
pip install -r requirements.txt
pytest                  # 全部 39 条
pytest -m api           # 仅 API（24 条）
pytest -m ui            # 仅 UI（15 条）
pytest -m ui --reruns 2 --reruns-delay 1   # UI 偶发重试
```

## 用例映射

| 目录 | 用例 |
|------|------|
| `tests/api/test_auth_api.py` | API-AUTH-001~003 |
| `tests/api/test_cart_api.py` | API-CART-001~009 |
| `tests/api/test_checkout_api.py` | API-CHK-001~005 |
| `tests/api/test_payment_api.py` | API-PAY/ORD |
| `tests/e2e/test_auth.py` | AUTH-001~002 |
| `tests/e2e/test_cart.py` | CART-001~005 |
| `tests/e2e/test_checkout_payment.py` | CHK/PAY/ORD UI |
