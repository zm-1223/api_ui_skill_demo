# Tigshop 演示站 — 购物车与支付测试用例计划

> 站点：[https://demo.tigshop.cn/](https://demo.tigshop.cn/)  
> 策略：接口覆盖核心逻辑，UI（POM）覆盖关键路径  
> 前置条件：[data/prerequisites.md](data/prerequisites.md)  
> 测试数据：[data/test_data.json](data/test_data.json)  
> 参考 Skill：ecommerce-cart-payment-tests

---

## 1. 环境与配置

| 配置项 | 值 |
|--------|-----|
| BASE_URL | `https://demo.tigshop.cn` |
| 测试账号 | `123123` / `123123`（**全部用例共用**） |
| 隐性等待 | 2s |
| 显性等待 | 2s |
| 登录等待 | 15s（UI 登录 / fallback） |
| 弹窗等待 | 3s |
| Token 复用 | `data/token.json` 或 `TIGSHOP_ACCESS_TOKEN` |
| 浏览器复用 | UI class 级 driver；API module 级 ui_browser |
| 默认商品 | `product_id=548`，`product_sn=SN0000548` |
| 商品页 URL | `/item/SN0000548` |
| 鉴权 | Cookie `accessToken` + `Authorization: Bearer <token>` |

### 范围说明

| 纳入 (In) | 排除 (Out) |
|-----------|------------|
| 登录、购物车、结算、支付、订单（功能） | Mock 接口 / Mock 支付 |
| API 契约 + 业务 code 断言 | 物流售后、发票、分销 |
| UI 关键路径（**POM 强制**） | **性能/压力/负载测试** |
| 真实沙箱/在线支付页 | 多账号并发 |

---

## 2. 用例数量总览

| 模块 | API 用例 | UI 用例 | 小计 | 优先级分布 |
|------|----------|---------|------|------------|
| 登录 | 3 | 2 | **5** | P0×4, P1×1 |
| 购物车 | 9 | 5 | **14** | P0×10, P1×4 |
| 结算 | 5 | 3 | **8** | P0×6, P1×2 |
| 支付 | 4 | 3 | **7** | P0×5, P1×2 |
| 订单 | 3 | 2 | **5** | P0×4, P1×1 |
| **合计** | **24** | **15** | **39** | P0×29, P1×10 |

### 分层原则

| 层级 | 数量 | 职责 |
|------|------|------|
| **API** | 24 | 金额、库存、状态机、错误码、支付状态 |
| **UI（POM）** | 15 | 页面跳转、角标/toast、弹窗、支付页操作 |

---

## 3. 模块用例清单

### 3.1 登录（5 条）

| ID | 优先级 | 层 | 标题 | 前置 | 关键数据 |
|----|--------|-----|------|------|----------|
| API-AUTH-001 | P0 | API | 会话共享 token 可用且通过 getCount 校验 | 已配置 token | `shared_access_token` fixture |
| API-AUTH-002 | P0 | API | 错误密码登录失败 | 无 | `negative.wrong_password` |
| API-AUTH-003 | P1 | API | 未登录访问购物车返回 401 | 无 token | `GET /api/cart/cart/list` |
| AUTH-001 | P0 | UI | 正确登录进入会员中心 | 打开登录页 | 同账号 + 勾选协议 |
| AUTH-002 | P0 | UI | 错误密码页面提示失败 | 打开登录页 | `wrong_password` |

**接口**：`POST /api/user/login/signin`  
**POM**：`LoginPage`

---

### 3.2 购物车（14 条）

| ID | 优先级 | 层 | 标题 | 前置 | 关键数据 |
|----|--------|-----|------|------|----------|
| API-CART-001 | P0 | API | 空购物车 getCount=0 | 已登录 + clear | — |
| API-CART-002 | P0 | API | UI 加购后 list 含商品 | 已登录 + clear | `product_sn=SN0000548` |
| API-CART-003 | P0 | API | 同 SKU 重复加购数量合并 | 已加购 1 件 | 再次加购，期望合并 |
| API-CART-004 | P0 | API | 修改数量合法 | 购物车有商品 | `update_qty_legal=2` |
| API-CART-005 | P1 | API | 修改数量超库存失败 | 购物车有商品 | `over_stock_qty=99999` |
| API-CART-006 | P0 | API | 删除单个商品 | 购物车有商品 | `cartId` 动态获取 |
| API-CART-007 | P0 | API | 清空购物车 | 购物车有商品 | `POST /api/cart/cart/clear` |
| API-CART-008 | P0 | API | 购物车金额汇总正确 | 已加购 | `subtotal = price × quantity` |
| API-CART-009 | P1 | API | 购物车列表字段完整 | 已加购 | cartId/productId/quantity/price |
| CART-001 | P0 | UI | 空购物车展示空态文案 | 已登录 + clear | 访问 `/cart` |
| CART-002 | P0 | UI | 加购后角标显示 1 | 已登录 | `/item/SN0000548` 加购 |
| CART-003 | P0 | UI | 重复加购角标累加 | 已加购 1 件 | 再次加购，角标=2 |
| CART-004 | P0 | UI | 删除商品后角标归零 | 购物车有 1 件 | 删除后 count=0 |
| CART-005 | P1 | UI | 购物车页金额与接口一致 | 已加购 | 页面合计 ≈ API total |

**主要接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cart/cart/getCount` | 角标数量（data 可能为 int） |
| POST | `/api/cart/cart/addToCart` | **接口加购**（body: id/number/sku_id） |
| GET | `/api/cart/cart/list` | 购物车列表（cartList/camelCase） |
| POST | `/api/cart/cart/updateItem` | 改数量 |
| POST | `/api/cart/cart/removeItem` | 删除 |
| POST | `/api/cart/cart/clear` | 清空 |
| POST | `/api/cart/cart/updateCheck` | 勾选状态 |

**POM**：`ProductPage`、`CartPage`

---

### 3.3 结算（8 条）

| ID | 优先级 | 层 | 标题 | 前置 | 关键数据 |
|----|--------|-----|------|------|----------|
| API-CHK-001 | P0 | API | 结算页金额与购物车一致 | 购物车有勾选商品 | `flow_type=1` |
| API-CHK-002 | P0 | API | 空车结算失败 | 已 clear | `flow_type=1` |
| API-CHK-003 | P0 | API | 提交订单生成 order_id | 结算数据完整 | `address_id` 动态获取 |
| API-CHK-004 | P1 | API | 默认地址与运费展示 | 有地址 + 有商品 | `shipping_fee` 字段 |
| API-CHK-005 | P1 | API | total_amount 计算正确 | 有商品 | 商品额 + 运费 |
| CHK-001 | P0 | UI | 结算页商品与金额展示 | 购物车有商品 | 去结算 |
| CHK-002 | P0 | UI | 提交订单跳转支付页 | 结算页就绪 | URL 含 `pay` |
| CHK-003 | P1 | UI | 价格变动弹窗确认后继续 | 可能触发变价 | 弹窗等待 3s |

**主要接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/order/check/index` | 获取结算信息 |
| POST | `/api/order/check/submit` | 提交订单 |

**POM**：`CheckoutPage`

---

### 3.4 支付（7 条）

| ID | 优先级 | 层 | 标题 | 前置 | 关键数据 |
|----|--------|-----|------|------|----------|
| API-PAY-001 | P0 | API | 支付页信息金额与订单一致 | 有待支付订单 | `order_id` |
| API-PAY-002 | P0 | API | 发起支付返回 pay_info | 有待支付订单 | `pay_type=yunpay_alipay` |
| API-PAY-003 | P0 | API | 支付成功后状态已支付 | 完成支付流程 | `check_status` |
| API-PAY-004 | P1 | API | 取消支付保持待支付 | 支付页取消 | `pay_status=0` |
| PAY-001 | P0 | UI | 支付成功页/订单状态文案 | 完成沙箱支付 | 待支付→已支付 |
| PAY-002 | P0 | UI | 取消支付可返回重试 | 支付页取消 | 仍为待支付 |
| PAY-003 | P1 | UI | 支付页订单金额展示正确 | 有待支付订单 | 金额与下单一致 |

**主要接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/order/pay/index?id={order_id}` | 支付页信息 |
| GET | `/api/order/pay/create?id={order_id}&type={pay_type}` | 发起支付 |
| GET | `/api/order/pay/check_status?id={order_id}` | 校验支付状态 |

**POM**：`PaymentPage`

---

### 3.5 订单（5 条）

| ID | 优先级 | 层 | 标题 | 前置 | 关键数据 |
|----|--------|-----|------|------|----------|
| API-ORD-001 | P0 | API | 下单后订单详情字段完整 | 已 submit | `order_id` |
| API-ORD-002 | P0 | API | 新建订单状态为待支付 | 刚提交 | `order_status_name=待支付` |
| API-ORD-003 | P1 | API | 取消支付后订单仍可查 | 支付取消后 | 状态不变 |
| ORD-001 | P0 | UI | 订单列表展示待支付状态 | 有待支付单 | `/member/order/list` |
| ORD-002 | P1 | UI | 支付成功后订单状态更新 | 支付完成 | 已支付文案 |

**POM**：`OrderPage`

---

## 4. 前置条件摘要

详见 [data/prerequisites.md](data/prerequisites.md)。

| 类别 | 要点 |
|------|------|
| 环境 | Python 3.9+、Chrome、可访问演示站 |
| 账号 | `123123` / `123123`，全部用例共用 |
| 地址 | 至少 1 条收货地址 |
| 隔离 | 每条用例前后 `clear` 购物车 |
| 登录 | UI 须勾选协议；API 可能需要 `accessToken` Cookie |
| 等待 | 隐性/显性 2s，弹窗 3s，禁止 sleep |
| POM | UI 禁止在 test 中写 locator |

---

## 5. 测试数据文件说明

详见 [data/test_data.json](data/test_data.json)。

| 节点 | 用途 |
|------|------|
| `env` | 站点 URL、页面路径、商品页模式 |
| `wait` | 隐性/显性/弹窗等待秒数 |
| `account` | 共用账号凭证 |
| `auth` | 登录接口、Cookie/Header 格式 |
| `products` | 默认商品 ID/SN、边界数量 |
| `checkout` | 结算/提交订单默认参数 |
| `payment` | 支付方式与期望状态文案 |
| `cleanup` | 清理接口路径 |
| `negative` | 负向测试数据 |

---

## 6. 工程目录与文件映射（已实现）

```
api/          → api/shop_api_client.py, api/auth_helper.py
config/       → config/settings.py
ui/           → ui/*_page.py（POM）
utils/        → utils/wait_helper.py, popup_helper.py, logger_helper.py
tests/api/    → API 用例 24 条
tests/e2e/    → UI 用例 15 条
reports/      → HTML 报告、失败截图
```

| 文件 | 用例 ID |
|------|---------|
| `tests/api/test_auth_api.py` | API-AUTH-001 ~ 003 |
| `tests/api/test_cart_api.py` | API-CART-001 ~ 009 |
| `tests/api/test_checkout_api.py` | API-CHK-001 ~ 005 |
| `tests/api/test_payment_api.py` | API-PAY-001 ~ 004, API-ORD-001 ~ 003 |
| `tests/e2e/test_auth.py` | AUTH-001 ~ 002 |
| `tests/e2e/test_cart.py` | CART-001 ~ 005 |
| `tests/e2e/test_checkout_payment.py` | CHK-001 ~ 003, PAY-001 ~ 003, ORD-001 ~ 002 |
| `ui/*.py` | POM 页面对象 |
| `api/shop_api_client.py` | API 封装 |

---

## 7. 执行命令与报告

```bash
pip install -r requirements.txt
pytest                              # 全部 39 条；生成 allure-results + report.html
python scripts/generate_allure_report.py   # 手动生成 Allure HTML
```

### 浏览器可打开的 HTML

| 类型 | 文件 | 依赖 |
|------|------|------|
| pytest-html | `reports/report.html` | 无，pytest 自动生成 |
| Allure | `reports/allure-report/index.html` | 需安装 Allure CLI |

pytest.ini 已配置：

- `--html=reports/report.html --self-contained-html`
- `--alluredir=reports/allure-results`

### Fixture 作用域（方案 3）

| 层级 | Fixture | scope | 效果 |
|------|---------|-------|------|
| 全局 | `shared_access_token` | session | 1 次 token 解析 |
| UI | `driver` / `logged_in_driver` | class | 每 TestClass 1 个 Chrome |
| UI 登录 | `driver` in `test_auth.py` | function | 登录用例互不污染 |
| API | `ui_browser` | module | 每 api 测试文件 1 个 Chrome |
| API | `ui_add_product_once` | function | 复用 browser，API 清车 + UI 加购 |
| 工具 | `BrowserHelper.chromedriver_path` | session | chromedriver 只 install 一次 |

## 8. Skill 检查清单对照

### 购物车 ✓

- [x] 空购物车（API-CART-001 / CART-001）
- [x] 单 SKU 加购（API-CART-002 / CART-002）
- [x] 同 SKU 合并（API-CART-003 / CART-003）
- [x] 改数量合法/超库存（API-CART-004 / 005）
- [x] 删除/清空（API-CART-006 / 007 / CART-004）
- [x] 金额汇总（API-CART-008 / CART-005）

### 结算 ✓

- [x] 金额一致（API-CHK-001 / CHK-001）
- [x] 运费展示（API-CHK-004）
- [x] 提交订单（API-CHK-003 / CHK-002）
- [x] 价格变动弹窗（CHK-003）

### 支付 ✓

- [x] 支付页信息（API-PAY-001 / PAY-003）
- [x] 发起支付（API-PAY-002）
- [x] 支付成功（API-PAY-003 / PAY-001）
- [x] 取消可重试（API-PAY-004 / PAY-002）

### 订单 ✓

- [x] 唯一 order_id（API-CHK-003）
- [x] 待支付状态（API-ORD-002 / ORD-001）
- [x] 支付后状态（ORD-002）

### 登录 ✓

- [x] 会话 token 复用（API-AUTH-001 / `shared_access_token`）
- [x] 正确/错误凭证（AUTH-001/002 仍走真实 UI 登录）
- [x] 错误密码 API（API-AUTH-002）
- [x] 未登录访问（API-AUTH-003）

---

## 9. 参考文档

- [Tigshop 演示站](https://demo.tigshop.cn/)
- [Tigshop Apifox — 登录](https://s.apifox.cn/7238ef42-8095-44b6-b0d9-7b701ce484b8/270300367e0)
- [Tigshop Apifox — 购物车列表](https://s.apifox.cn/7238ef42-8095-44b6-b0d9-7b701ce484b8/270300346e0)
- [Tigshop Apifox — 结算](https://s.apifox.cn/7238ef42-8095-44b6-b0d9-7b701ce484b8/270300317e0)
- [Tigshop Apifox — 订单提交](https://s.apifox.cn/7238ef42-8095-44b6-b0d9-7b701ce484b8/270300320e0)
- [Tigshop Apifox — 支付](https://s.apifox.cn/7238ef42-8095-44b6-b0d9-7b701ce484b8/270300322e0)
