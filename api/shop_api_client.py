"""Tigshop REST API 客户端：封装购物车/结算/支付/订单接口，供 tests/api 调用。"""
import logging  # 框架标准库：日志

import requests  # 第三方 requests：HTTP 客户端

from api.auth_helper import AuthHelper  # 自定义调用：鉴权辅助
from config.settings import config  # 自定义调用：全局配置

logger = logging.getLogger("tigshop_test.api")  # 框架 logging：API logger


class ShopApiClient:
    """每个用例独立 Session，断言顺序：HTTP status -> code -> data。"""

    def __init__(self, token: str | None = None) -> None:
        """创建 Session；若传入 token 则注入鉴权。"""
        self.session = requests.Session()  # 第三方 requests：保持 Cookie 的会话
        self.session.headers.update({"Content-Type": "application/json"})  # 框架：默认 JSON 头
        if token:  # 自定义：有 token 则应用
            AuthHelper.apply_token(self.session, token)  # 自定义调用：写 Cookie+Header

    @staticmethod
    def assert_ok(resp: requests.Response) -> dict:
        """断言 HTTP 200 且业务 code=0，返回 data 字段。"""
        assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"  # pytest 断言
        body = resp.json()  # 第三方 requests：解析 JSON
        code = body.get("code")  # 自定义：业务码字段
        assert code == 0, f"业务 code={code}, msg={body.get('message') or body.get('msg')}"  # 断言
        data = body.get("data")  # 取 data 节点
        if data is None:  # 无 data
            return {}  # 空 dict
        if isinstance(data, dict):  # dict 直接返回
            return data  # 返回
        return {"value": data}  # int/str 等包装为 value 便于统一读取

    @staticmethod
    def assert_fail(resp: requests.Response, expected_code: int | None = None) -> dict:
        """断言业务失败（code != 0），可选校验具体错误码。"""
        assert resp.status_code == 200, f"HTTP {resp.status_code}"  # HTTP 仍可能 200
        body = resp.json()  # 解析 JSON
        code = body.get("code")  # 业务码
        assert code != 0, "期望失败但 code=0"  # 自定义断言
        if expected_code is not None:  # 可选精确错误码
            assert code == expected_code, f"期望 code={expected_code}, 实际={code}"  # 断言
        return body  # 返回完整 body

    @staticmethod
    def pick_field(data: dict, *names: str, default=None):
        """从 dict 按 camelCase/snake_case 多个候选键取值。"""
        for name in names:  # 依次尝试
            if name in data and data[name] is not None:  # 命中
                return data[name]  # 返回值
        return default  # 均未命中

    @staticmethod
    def parse_cart_count(data) -> int:
        """解析 getCount 的 data：演示站可能返回 int 或 {count: n}。"""
        if isinstance(data, int):  # 直接返回数量
            return data  # int
        if isinstance(data, dict):  # dict 包装
            val = ShopApiClient.pick_field(data, "count", "value", default=0)  # 多键
            return int(val or 0)  # 转 int
        return 0  # 兜底 0

    @staticmethod
    def normalize_cart_item(item: dict | None) -> dict | None:
        """为购物车行补充 snake_case 别名，兼容旧用例字段名。"""
        if not item:  # 空
            return item  # 原样
        out = dict(item)  # 复制
        aliases = {  # camelCase -> snake_case
            "cartId": "cart_id",
            "productId": "product_id",
            "productSn": "product_sn",
            "productPrice": "product_price",
        }
        for camel, snake in aliases.items():  # 补别名
            if camel in item and snake not in out:  # 有 camel 无 snake
                out[snake] = item[camel]  # 写入别名
        return out  # 返回增强 dict

    def login(self, username: str | None = None, password: str | None = None) -> dict:
        """POST /api/user/login/signin；演示站可能返回 1002 需验证码。"""
        body = dict(config.login_body)  # 自定义：复制登录模板
        if username:  # 覆盖用户名
            body["username"] = username
        if password:  # 覆盖密码
            body["password"] = password
        url = config.api_url("/user/login/signin")  # 自定义：拼接登录 URL
        logger.info("API 登录: %s", url)  # 日志
        return self.session.post(url, json=body, timeout=30).json()  # 第三方 requests：POST

    def get_cart_count(self) -> requests.Response:
        """GET /api/cart/cart/getCount 购物车角标。"""
        url = config.api_url("/cart/cart/getCount")  # camelCase 路径
        return self.session.get(url, timeout=30)  # GET 请求

    def get_cart_count_value(self) -> int:
        """getCount 并解析为 int 数量。"""
        data = self.assert_ok(self.get_cart_count())  # 自定义：断言成功
        return self.parse_cart_count(data)  # 自定义：解析数量

    def get_cart_list(self) -> requests.Response:
        """GET /api/cart/cart/list 购物车列表。"""
        url = config.api_url("/cart/cart/list")  # 列表接口
        return self.session.get(url, timeout=30)  # GET

    def add_to_cart(
        self,
        product_id: int | None = None,
        quantity: int = 1,
        sku_id: int = 0,
        is_quick: int = 0,
    ) -> requests.Response:
        """POST /api/cart/cart/addToCart 接口加购（比 UI 加购更稳定）。"""
        url = config.api_url("/cart/cart/addToCart")  # 加购接口
        payload = {
            "id": product_id or config.product_id,  # 商品 ID
            "number": quantity,  # 数量
            "sku_id": sku_id,  # SKU（无规格为 0）
            "is_quick": is_quick,  # 非立即购买
        }
        logger.info("API 加购: product_id=%s qty=%s", payload["id"], quantity)  # 日志
        return self.session.post(url, json=payload, timeout=30)  # POST JSON

    def clear_cart(self) -> requests.Response:
        """POST /api/cart/cart/clear 清空购物车。"""
        url = config.api_url("/cart/cart/clear")  # 清空接口
        return self.session.post(url, timeout=30)  # POST

    def update_item(self, cart_id: int | str, quantity: int) -> requests.Response:
        """POST /api/cart/cart/updateItem 修改数量。"""
        url = config.api_url("/cart/cart/updateItem")  # 改数量
        payload = {"cartId": str(cart_id), "data": {"quantity": quantity}}  # Tigshop 请求体
        return self.session.post(url, json=payload, timeout=30)  # POST JSON

    def remove_item(self, cart_id: int | str) -> requests.Response:
        """POST /api/cart/cart/removeItem 删除商品。"""
        url = config.api_url("/cart/cart/removeItem")  # 删除接口
        return self.session.post(url, data={"cartIds": str(cart_id)}, timeout=30)  # form-data

    def update_check(self, check_data: list | None = None) -> requests.Response:
        """POST /api/cart/cart/updateCheck 更新勾选状态。"""
        url = config.api_url("/cart/cart/updateCheck")  # 勾选
        payload = {"data": check_data or []}  # 默认空列表全选由前端逻辑处理
        return self.session.post(url, json=payload, timeout=30)  # POST

    def checkout_index(self, flow_type: int | None = None) -> requests.Response:
        """POST /api/order/check/index 获取结算信息。"""
        url = config.api_url("/order/check/index")  # 结算页数据
        ft = flow_type if flow_type is not None else config.flow_type  # flow_type
        return self.session.post(url, data={"flow_type": str(ft)}, timeout=30)  # multipart

    def checkout_submit(
        self,
        address_id: int,
        shipping_type: list | None = None,
        pay_type_id: int | None = None,
    ) -> requests.Response:
        """POST /api/order/check/submit 提交订单。"""
        url = config.api_url("/order/check/submit")  # 提交订单
        payload = {
            "address_id": address_id,  # 收货地址 ID
            "shipping_type": shipping_type or config.shipping_type,  # 配送方式
            "pay_type_id": pay_type_id or config.pay_type_id,  # 支付方式
            "use_point": 0,  # 不使用积分
            "use_balance": 0,  # 不使用余额
            "flow_type": config.flow_type,  # 普通购物车
        }
        return self.session.post(url, json=payload, timeout=30)  # POST JSON

    def pay_index(self, order_id: int | str) -> requests.Response:
        """GET /api/order/pay/index 支付页信息。"""
        url = config.api_url(f"/order/pay/index?id={order_id}")  # 查询参数 id
        return self.session.get(url, timeout=30)  # GET

    def pay_create(self, order_id: int | str, pay_type: str | None = None) -> requests.Response:
        """GET /api/order/pay/create 发起支付。"""
        pt = pay_type or config.pay_type  # 支付类型
        url = config.api_url(f"/order/pay/create?id={order_id}&type={pt}")  # 发起支付 URL
        return self.session.get(url, timeout=30)  # GET

    def pay_check_status(self, order_id: int | str) -> requests.Response:
        """GET /api/order/pay/check_status 校验支付状态。"""
        url = config.api_url(f"/order/pay/check_status?id={order_id}")  # 状态查询
        return self.session.get(url, timeout=30)  # GET

    def product_detail(self, product_id: int | None = None) -> requests.Response:
        """GET /api/product/product/detail 商品详情。"""
        pid = product_id or config.product_id  # 商品 ID
        url = config.api_url(f"/product/product/detail?id={pid}")  # 详情 URL
        return self.session.get(url, timeout=30)  # GET

    def first_cart_item(self) -> dict | None:
        """从 list 响应中取第一条购物车商品（兼容 cartList/cart_list）。"""
        data = self.assert_ok(self.get_cart_list())  # 自定义：拉列表并断言成功
        shops = data.get("cartList") or data.get("cart_list") or []  # 店铺分组
        for shop in shops:  # 遍历店铺
            rows = shop.get("carts") or shop.get("cart_list") or []  # 行项目
            for item in rows:  # 遍历行
                return self.normalize_cart_item(item)  # 返回带别名条目
        return None  # 空车返回 None

    def first_address_id(self, checkout_data: dict | None = None) -> int:
        """从 checkout_index 数据取第一个 addressId。"""
        chk = checkout_data if checkout_data is not None else self.assert_ok(self.checkout_index())  # 结算
        addresses = chk.get("addressList") or chk.get("address_list") or []  # 地址列表
        assert addresses, "账号需至少一条收货地址"  # 前置检查
        addr = addresses[0]  # 第一条
        aid = self.pick_field(addr, "addressId", "address_id")  # 多键取值
        assert aid is not None, "地址缺少 addressId"  # 断言
        return int(aid)  # 返回 int

    def extract_order_id(self, submit_data: dict) -> int:
        """从 submit 响应取 orderId/order_id。"""
        oid = self.pick_field(submit_data, "orderId", "order_id")  # 多键
        assert oid is not None, f"submit 响应无 orderId: {submit_data}"  # 断言
        return int(oid)  # 返回 int

    @classmethod
    def with_ui_token(cls) -> "ShopApiClient":
        """通过缓存 token 返回已鉴权客户端（不重复 UI 登录）。"""
        token = AuthHelper.get_token()  # 自定义：复用 token
        return cls(token=token)  # 构造客户端
