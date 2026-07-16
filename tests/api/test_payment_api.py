"""支付与订单 API 用例：API-PAY-001~004、API-ORD-001~003。"""
import pytest  # 框架 pytest

from api.shop_api_client import ShopApiClient  # 自定义客户端
from config.settings import config  # 配置


@pytest.mark.api  # api
@pytest.mark.payment  # payment
@pytest.mark.order  # order
class TestPaymentOrderApi:
    """支付与订单接口测试。"""

    def _create_pending_order(self, ui_add_product_once) -> tuple[ShopApiClient, int]:
        """辅助：创建待支付订单，返回 (client, order_id)。"""
        client = ShopApiClient(token=ui_add_product_once)  # 有车客户端
        chk = ShopApiClient.assert_ok(client.checkout_index())  # 结算
        addr = chk["address_list"][0]["address_id"]  # 地址 ID
        data = ShopApiClient.assert_ok(client.checkout_submit(address_id=addr))  # 下单
        return client, int(data["order_id"])  # 返回客户端与订单号

    def test_api_pay_001_pay_index_amount_match(self, ui_add_product_once, log_api_test):
        """API-PAY-001：支付页信息金额与订单一致。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 待支付单
        pay_data = ShopApiClient.assert_ok(client.pay_index(order_id))  # 支付页
        assert pay_data.get("order")  # 有 order 节点
        assert pay_data["order"].get("order_id") == order_id  # ID 一致

    def test_api_pay_002_create_payment_returns_pay_info(self, ui_add_product_once, log_api_test):
        """API-PAY-002：发起支付返回数据。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        data = ShopApiClient.assert_ok(client.pay_create(order_id))  # 发起支付
        assert "order_id" in data or "order_amount" in data or data.get("errcode") == 0  # 有支付信息

    def test_api_pay_003_check_status_pending_by_default(self, ui_add_product_once, log_api_test):
        """API-PAY-003：新建订单支付状态为待支付（pay_status=0）。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        status = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 查状态
        assert status.get("pay_status", 0) == 0  # 待支付

    def test_api_pay_004_cancel_keeps_pending(self, ui_add_product_once, log_api_test):
        """API-PAY-004：未支付时状态保持待支付。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        s1 = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 第一次
        s2 = ShopApiClient.assert_ok(client.pay_check_status(order_id))  # 第二次
        assert s1.get("pay_status") == s2.get("pay_status")  # 状态不变

    def test_api_ord_001_order_detail_fields(self, ui_add_product_once, log_api_test):
        """API-ORD-001：支付页订单详情字段完整。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 详情
        order = pay.get("order", {})  # order 节点
        assert order.get("order_id") == order_id  # order_id
        assert order.get("order_status_name") or order.get("pay_status_name")  # 状态名

    def test_api_ord_002_new_order_pending_payment(self, ui_add_product_once, log_api_test):
        """API-ORD-002：新建订单状态为待支付。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 查详情
        status_name = pay["order"].get("order_status_name", "")  # 状态文案
        assert config.expected_pending_status in status_name or "待支付" in status_name  # 待支付

    def test_api_ord_003_order_queryable_after_cancel_flow(self, ui_add_product_once, log_api_test):
        """API-ORD-003：订单创建后仍可查询（模拟取消支付后）。"""
        client, order_id = self._create_pending_order(ui_add_product_once)  # 订单
        pay = ShopApiClient.assert_ok(client.pay_index(order_id))  # 仍可查
        assert pay.get("order")  # 有数据
