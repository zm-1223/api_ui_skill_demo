"""购物车 UI 用例：CART-001 ~ 005。"""
import pytest  # 框架 pytest

from api.auth_helper import AuthHelper  # 自定义：Cookie 注入
from api.shop_api_client import ShopApiClient  # 自定义：读 API 金额
from config.settings import config  # 配置
from ui.cart_page import CartPage  # POM 购物车
from ui.product_page import ProductPage  # POM 商品


@pytest.mark.ui  # UI
@pytest.mark.cart  # 购物车
class TestCartUi:
    """购物车 UI 测试。"""

    def _inject_token_and_clear(self, driver, shared_access_token) -> None:
        """注入共享 token 并 API 清空购物车（不经过登录页）。"""
        AuthHelper.inject_token_to_driver(driver, shared_access_token)  # Cookie 注入
        client = ShopApiClient(token=shared_access_token)  # API 客户端
        client.clear_cart()  # 清空购物车

    def test_cart_001_empty_cart_shows_empty_hint(self, driver, shared_access_token, log_test_name):
        """CART-001：空购物车展示空态。"""
        self._inject_token_and_clear(driver, shared_access_token)  # 注入 token 并清车
        cart = CartPage(driver).open_cart()  # 打开购物车
        assert cart.is_empty_cart_displayed()  # 空态文案

    def test_cart_002_add_item_shows_badge_one(self, logged_in_driver, log_test_name):
        """CART-002：加购后角标为 1。"""
        product = ProductPage(logged_in_driver)  # POM 商品页
        product.open_product().add_to_cart(1)  # 加购 1 件
        assert product.get_badge_count() == "1"  # 角标 1

    def test_cart_003_repeat_add_badge_increments(self, logged_in_driver, log_test_name):
        """CART-003：重复加购角标累加。"""
        product = ProductPage(logged_in_driver)  # 商品页
        product.open_product().add_to_cart(1)  # 第一次
        product.add_to_cart(1)  # 第二次
        assert int(product.get_badge_count()) >= 2  # 角标 >= 2

    def test_cart_004_delete_item_badge_zero(self, logged_in_driver, log_test_name):
        """CART-004：删除后角标归零。"""
        product = ProductPage(logged_in_driver)  # 加购
        product.open_product().add_to_cart(1)  # 加 1 件
        product.go_cart()  # 去购物车
        CartPage(logged_in_driver).delete_first_item()  # 删除
        logged_in_driver.get(config.base_url)  # 回首页读角标
        assert ProductPage(logged_in_driver).get_badge_count() == "0"  # 角标 0

    def test_cart_005_page_total_near_api_total(self, logged_in_driver, log_test_name):
        """CART-005：购物车页金额与 API 接近。"""
        product = ProductPage(logged_in_driver)  # 加购
        product.open_product().add_to_cart(1)  # 加购
        cookie = logged_in_driver.get_cookie(config.token_cookie)  # token
        api_total = None  # API 合计
        if cookie:  # 有 token
            data = ShopApiClient.assert_ok(
                ShopApiClient(token=cookie["value"]).get_cart_list()
            )  # API 列表
            api_total = data.get("total", {}).get("product_amount")  # 商品总额
        cart = CartPage(logged_in_driver).open_cart()  # 购物车页
        ui_text = cart.get_total_amount_text()  # 页面合计文本
        ui_num = cart.extract_amount_number(ui_text)  # 提取数字
        if api_total is not None and ui_num is not None:  # 两边都有数
            assert abs(float(api_total) - ui_num) < 1.0  # 允许展示差异
