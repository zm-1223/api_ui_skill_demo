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
        return body.get("data") or {}  # 返回 data，空则 {}

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

    def get_cart_list(self) -> requests.Response:
        """GET /api/cart/cart/list 购物车列表。"""
        url = config.api_url("/cart/cart/list")  # 列表接口
        return self.session.get(url, timeout=30)  # GET

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
        """从 list 响应中取第一条购物车商品。"""
        data = self.assert_ok(self.get_cart_list())  # 自定义：拉列表并断言成功
        for shop in data.get("cart_list", []):  # 遍历店铺分组
            for item in shop.get("carts", []):  # 遍历购物车行
                return item  # 返回第一条
        return None  # 空车返回 None

    @classmethod
    def with_ui_token(cls) -> "ShopApiClient":
        """通过缓存 token 返回已鉴权客户端（不重复 UI 登录）。"""
        token = AuthHelper.get_token()  # 自定义：复用 token
        return cls(token=token)  # 构造客户端
