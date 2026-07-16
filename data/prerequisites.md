# Tigshop 演示站 — 测试前置条件

> 目标站点：[https://demo.tigshop.cn/](https://demo.tigshop.cn/)  
> 测试数据：[test_data.json](./test_data.json)  
> 用例计划：[case.md](../case.md)

---

## 1. 环境前置

| 项 | 要求 |
|----|------|
| 网络 | 可访问 `https://demo.tigshop.cn` |
| Python | 3.9+ |
| 浏览器 | Chrome / Edge（UI 用例） |
| 依赖 | `pytest`、`requests`、`selenium`、`pytest-html`、`webdriver-manager` |
| 范围外 | 性能/压力/负载测试（本 Skill 不做） |

---

## 2. 账号前置

| 项 | 值 |
|----|-----|
| 用户名 | `123123` |
| 密码 | `123123` |
| 策略 | **全部 39 条用例共用此账号** |
| 登录页 | `/member/login` |
| 登录接口 | `POST /api/user/login/signin` |
| 登录态 | Cookie `accessToken` + Header `Authorization: Bearer <token>` |

### 登录注意

- UI 登录须勾选「我已阅读并同意《服务协议》和《隐私协议》」
- 直接调登录 API 可能触发行为验证码（`code=1002`），**推荐方案 B：手动复制 `accessToken` 后复用**
- 自动化默认 `token_cache.allow_ui_login_fallback=false`，无 token 时会明确报错并提示配置方式

### Token 复用（方案 B）

| 项 | 说明 |
|----|------|
| 缓存文件 | `data/token.json`（`access_token` 或 `token` 字段，已 gitignore） |
| 环境变量 | `TIGSHOP_ACCESS_TOKEN` |
| 校验接口 | `GET /api/cart/cart/getCount`（`code=0` 视为有效） |
| 会话 fixture | `shared_access_token`（`tests/conftest.py`，scope=session） |
| API 注入 | `ShopApiClient(token=shared_access_token)` |
| UI 注入 | `AuthHelper.inject_token_to_driver(driver, token)` → `refresh()` |
| 登录等待 | `token_cache.login_wait_sec=15`（仅 UI 登录/fallback 使用） |

**获取 token 步骤**：浏览器用 `123123`/`123123` 登录 → F12 → Application → Cookies → `demo.tigshop.cn` → 复制 `accessToken` → 粘贴到 `data/token.json`。

---

## 3. 等待策略

| 类型 | 超时 | 说明 |
|------|------|------|
| 隐性等待 | **2s** | `driver.implicitly_wait(2)`，fixture 初始化一次 |
| 显性等待 | **2s** | Page 内 `WebDriverWait(driver, 2)` |
| 登录等待 | **15s** | `LoginPage.wait_login_success` / UI fallback 专用 |
| 弹窗等待 | **3s** | Cookie/协议/价格变动等局部处理 |
| 禁止 | `time.sleep()` | 使用 Selenium 等待机制 |

### 3.1 Fixture 作用域（提速）

| Fixture | 作用域 | 文件 |
|---------|--------|------|
| `shared_access_token` | session | `tests/conftest.py` |
| `driver` / `logged_in_driver` | class | `tests/e2e/conftest.py` |
| `driver`（登录专项） | function | `tests/e2e/test_auth.py` |
| `ui_browser` | module | `tests/api/conftest.py` |
| `ui_add_product_once` | function | `tests/api/conftest.py` |
| ChromeDriver 路径 | session | `utils/browser_helper.py` |

UI class 内每条用例前 autouse `clear_cart`；API `ui_add_product_once` 每条 setup/teardown 亦清车。

---

## 4. 数据前置

### 4.1 默认商品

| 字段 | 值 | 说明 |
|------|-----|------|
| product_id | `548` | 接口加购/详情用 |
| product_sn | `SN0000548` | UI 商品页 `/item/SN0000548` |
| 详情接口 | `GET /api/product/product/detail?id=548` | 执行前确认商品在售 |

### 4.2 收货地址

- 账号需至少有 **1 条可用收货地址**
- `address_id` 由 `POST /api/order/check/index` 响应动态获取

### 4.3 购物车隔离

每条用例 **setup / teardown**：

1. 复用会话级 `shared_access_token`（**不重复 UI 登录**）
2. `POST /api/cart/cart/clear` 清空购物车

---

## 5. Tigshop 接口约定

| 说明 | 约定 |
|------|------|
| 路径风格 | **camelCase**（如 `getCount`，非 `get_count`） |
| 成功码 | `code = 0` |
| 商品页路由 | `/item/{productSn}`，非 `/product/{id}` |

### 核心 API 清单

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/user/login/signin` | 登录 |
| GET | `/api/product/product/detail?id={id}` | 商品详情 |
| GET | `/api/cart/cart/getCount` | 购物车角标 |
| GET | `/api/cart/cart/list` | 购物车列表 |
| POST | `/api/cart/cart/clear` | 清空购物车 |
| POST | `/api/cart/cart/updateItem` | 改数量 |
| POST | `/api/cart/cart/removeItem` | 删除商品 |
| POST | `/api/cart/cart/updateCheck` | 勾选状态 |
| POST | `/api/order/check/index` | 结算信息 |
| POST | `/api/order/check/submit` | 提交订单 |
| GET | `/api/order/pay/index?id={order_id}` | 支付页信息 |
| GET | `/api/order/pay/create?id={order_id}&type={pay_type}` | 发起支付 |
| GET | `/api/order/pay/check_status?id={order_id}` | 校验支付状态 |

---

## 6. UI 弹窗处理（POM 局部）

| 触发步骤 | 弹窗 | 处理 | 等待 |
|----------|------|------|------|
| 打开首页/商品页 | Cookie/用户协议 | 同意或关闭 | 3s |
| 登录页 | 服务协议勾选 | 勾选后再点登录 | 2s |
| 提交订单 | 价格变动确认 | 点击确认继续 | 3s |
| 加购成功 | Toast 提示 | 等待出现后继续 | 2s |

---

## 7. POM 页面映射

| Page 类 | 路由 |
|---------|------|
| `LoginPage` | `/member/login` |
| `ProductPage` | `/item/{product_sn}` |
| `CartPage` | `/cart` |
| `CheckoutPage` | `/order/check` |
| `PaymentPage` | `/order/pay` |
| `OrderPage` | `/member/order/list` |

---

## 8. 执行顺序建议

```
配置 token（一次性）→ 登录(API/UI) → 购物车(API/UI) → 结算(API/UI) → 支付(API/UI) → 订单(API/UI)
```

支付成功类用例放模块末尾，避免影响待支付状态断言。

---

## 9. 产出物

| 产出 | 路径 |
|------|------|
| pytest-html 报告 | `reports/report.html` |
| Allure 原始结果 | `reports/allure-results/` |
| Allure HTML 报告 | `reports/allure-report/index.html` |
| 日志 | `logs/test_*.log` |
| UI 失败截图 | `reports/screenshots/` |
