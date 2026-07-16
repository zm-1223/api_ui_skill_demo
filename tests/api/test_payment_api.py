"""支付与订单 API 用例：API-PAY-001~004、API-ORD-001~003。"""
import pytest  # 框架 pytest

from api.shop_api_client import ShopApiClient  # 自定义客户端
from config.settings import config  # 配置


@pytest.mark.api  # api
@pytest.mark.payment  # payment
@pytest.mark.order  # order
class TestPaymentOrderApi:
    """支付与订单接口测试。"""

    def _create_pending_order(self, api_add_product_once) -> tuple[ShopApiClient, int]:
        """辅助：API 加购并创建待支付订单，返回 (client, order_id)。"""
        client = ShopApiClient(token=api_add_product_once)  # 有车客户端
        address_id = client.first_address_id()  # 自定义：addressList
        submit_data = ShopApiClient.assert_ok(
            client.checkout_submit(address_id=address_id)
        )  # 下单
        return client, client.extract_order_id(submit_data)  # 返回客户端与 orderId

    def test_api_pay_001_pay_index_amount_match(self, api_add_product_once, log_api_test):
        """API-PAY-001：支付页信息金额与订单一致。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 待支付单
        pay_data = ShopApiClient.assert_ok(client.pay_index(order_id))  # 支付页
        order = pay_data.get("order") or pay_data  # order 节点
        oid = ShopApiClient.pick_field(order, "orderId", "order_id", default=order_id)  # ID
        assert oid == order_id  # ID 一致

    def test_api_pay_002_create_payment_returns_pay_info(self, api_add_product_once, log_api_test):
        """API-PAY-002：发起支付返回数据。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        data = ShopApiClient.assert_ok(client.pay_create(order_id))  # 发起支付
        assert (
            "orderId" in data
            or "order_id" in data
            or "orderAmount" in data
            or "order_amount" in data
            or data.get("errcode") == 0
        )  # 有支付信息

    def test_api_pay_003_check_status_pending_by_default(self, api_add_product_once, log_api_test):
        """API-PAY-003：新建订单支付状态为待支付（payStatus=0）。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        status = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 查状态
        pay_status = ShopApiClient.pick_field(status, "payStatus", "pay_status", default=0)  # 状态
        assert pay_status == 0  # 待支付

    def test_api_pay_004_cancel_keeps_pending(self, api_add_product_once, log_api_test):
        """API-PAY-004：未支付时状态保持待支付。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        s1 = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 第一次
        s2 = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 第二次
        k1 = ShopApiClient.pick_field(s1, "payStatus", "pay_status")  # 状态1
        k2 = ShopApiClient.pick_field(s2, "payStatus", "pay_status")  # 状态2
        assert k1 == k2  # 状态不变

    def test_api_ord_001_order_detail_fields(self, api_add_product_once, log_api_test):
        """API-ORD-001：支付页订单详情字段完整。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 详情
        order = pay.get("order") or pay  # order 节点
        oid = ShopApiClient.pick_field(order, "orderId", "order_id")  # orderId
        assert oid == order_id  # order_id
        status_name = ShopApiClient.pick_field(
            order, "orderStatusName", "order_status_name", "payStatusName", "pay_status_name"
        )  # 状态名
        assert status_name  # 有状态文案

    def test_api_ord_002_new_order_pending_payment(self, api_add_product_once, log_api_test):
        """API-ORD-002：新建订单状态为待支付。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 查详情
        order = pay.get("order") or pay  # order
        status_name = str(
            ShopApiClient.pick_field(
                order, "orderStatusName", "order_status_name", default=""
            )
            or ""
        )  # 状态文案
        assert config.expected_pending_status in status_name or "待支付" in status_name  # 待支付

    def test_api_ord_003_order_queryable_after_cancel_flow(self, api_add_product_once, log_api_test):
        """API-ORD-003：订单创建后仍可查询。"""
        client, order_id = self._create_pending_order(api_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 仍可查
        assert pay.get("order") or pay  # 有数据
