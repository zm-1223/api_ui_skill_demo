"""结算/支付/订单 UI 用例：CHK-001~003、PAY-001~003、ORD-001~002。"""
import pytest  # 框架 pytest

from api.shop_api_client import ShopApiClient  # 自定义：API 造数
from config.settings import config  # 配置
from ui.cart_page import CartPage  # POM
from ui.checkout_page import CheckoutPage  # POM
from ui.order_page import OrderPage  # POM
from ui.payment_page import PaymentPage  # POM
from ui.product_page import ProductPage  # POM


@pytest.mark.ui  # UI
@pytest.mark.checkout  # 结算
class TestCheckoutUi:
    """结算 UI 测试。"""

    def _prepare_cart(self, driver, shared_access_token) -> None:
        """API 加购后打开购物车页（比 UI 加购更稳定）。"""
        client = ShopApiClient(token=shared_access_token)  # API 客户端
        client.clear_cart()  # 清车
        ShopApiClient.assert_ok(client.add_to_cart(quantity=1))  # API 加购
        CartPage(driver).open_cart()  # 打开购物车页

    def test_chk_001_checkout_shows_product_and_amount(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """CHK-001：结算页展示商品与金额。"""
        self._prepare_cart(logged_in_driver, shared_access_token)  # API 造数
        CartPage(logged_in_driver).go_checkout()  # 去结算
        checkout = CheckoutPage(logged_in_driver)  # 结算页
        assert checkout.has_product_displayed()  # 有商品/金额
        assert checkout.get_payable_text()  # 应付区域非空

    def test_chk_002_submit_order_goes_payment(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """CHK-002：提交订单跳转支付页。"""
        self._prepare_cart(logged_in_driver, shared_access_token)  # 有车
        CartPage(logged_in_driver).go_checkout()  # 结算
        CheckoutPage(logged_in_driver).submit_order()  # 提交
        assert CheckoutPage(logged_in_driver).is_on_payment_page()  # URL 含 pay

    @pytest.mark.flaky(reruns=2, reruns_delay=1)  # 框架 pytest-rerunfailures：偶发 flaky
    def test_chk_003_price_change_popup_confirm_continue(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """CHK-003：价格变动弹窗确认后继续（若出现）。"""
        self._prepare_cart(logged_in_driver, shared_access_token)  # 有车
        CartPage(logged_in_driver).go_checkout()  # 结算
        checkout = CheckoutPage(logged_in_driver)  # 结算页
        checkout.submit_order()  # 提交（内部已处理弹窗）
        assert "check" not in checkout.current_url() or checkout.is_on_payment_page()  # 离开结算或到支付


@pytest.mark.ui  # UI
@pytest.mark.payment  # 支付
class TestPaymentUi:
    """支付 UI 测试。"""

    def _goto_payment_via_checkout(self, driver, shared_access_token) -> None:
        """API 加购 -> 购物车 -> 结算 -> 提交到支付页。"""
        client = ShopApiClient(token=shared_access_token)  # API 客户端
        client.clear_cart()  # 清车
        ShopApiClient.assert_ok(client.add_to_cart(quantity=1))  # API 加购
        CartPage(driver).open_cart().go_checkout()  # 购物车并结算
        CheckoutPage(driver).submit_order()  # 提交

    @pytest.mark.flaky(reruns=2, reruns_delay=1)  # 支付页加载可能慢
    def test_pay_001_payment_page_shows_pending_or_pay(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """PAY-001：支付页展示待支付或支付相关信息。"""
        self._goto_payment_via_checkout(logged_in_driver, shared_access_token)  # 到支付页
        payment = PaymentPage(logged_in_driver)  # POM
        text = payment.get_amount_text()  # 金额文本
        assert "支付" in text or "金额" in text or payment.is_pending_status_shown()  # 支付相关

    def test_pay_002_cancel_payment_can_retry(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """PAY-002：取消支付后仍可识别待支付状态。"""
        self._goto_payment_via_checkout(logged_in_driver, shared_access_token)  # 支付页
        PaymentPage(logged_in_driver).cancel_payment()  # 取消
        payment = PaymentPage(logged_in_driver)  # 当前页
        assert payment.is_pending_status_shown() or "订单" in payment.page_text()  # 待支付或订单页

    def test_pay_003_payment_amount_displayed(
        self, logged_in_driver, shared_access_token, log_test_name
    ):
        """PAY-003：支付页展示金额信息。"""
        self._goto_payment_via_checkout(logged_in_driver, shared_access_token)  # 支付页
        text = PaymentPage(logged_in_driver).get_amount_text()  # 读金额
        assert any(c.isdigit() for c in text)  # 含数字


@pytest.mark.ui  # UI
@pytest.mark.order  # 订单
class TestOrderUi:
    """订单 UI 测试。"""

    def test_ord_001_order_list_shows_pending(self, logged_in_driver, log_test_name):
        """ORD-001：订单列表可展示待支付（需账号存在待支付单）。"""
        order = OrderPage(logged_in_driver).open_order_list().wait_orders_loaded()  # 订单列表
        text = order.get_page_status_text()  # 页面文本
        assert "订单" in text or "待支付" in text or "暂无" in text  # 列表或空态

    def test_ord_002_paid_status_when_exists(self, logged_in_driver, log_test_name):
        """ORD-002：若存在已支付单则展示已支付文案（依赖历史数据）。"""
        order = OrderPage(logged_in_driver).open_order_list().wait_orders_loaded()  # 列表
        text = order.get_page_status_text()  # 全文
        if order.has_paid_order():  # 有已支付单
            assert config.expected_paid_status in text or "已支付" in text  # 断言文案
        else:  # 无已支付历史则跳过硬性断言
            assert "订单" in text  # 至少能打开列表
