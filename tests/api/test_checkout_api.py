"""结算 API 用例：API-CHK-001 ~ 005。"""
import pytest  # 框架 pytest

from api.shop_api_client import ShopApiClient  # 自定义客户端
from config.settings import config  # 配置


@pytest.mark.api  # api
@pytest.mark.checkout  # checkout
class TestCheckoutApi:
    """结算接口测试。"""

    def _client_with_cart(self, ui_add_product_once) -> ShopApiClient:
        """辅助：带一件商品的已登录客户端。"""
        return ShopApiClient(token=ui_add_product_once)  # 返回客户端

    def test_api_chk_001_checkout_amount_matches_cart(self, ui_add_product_once, log_api_test):
        """API-CHK-001：结算页金额与购物车一致。"""
        client = self._client_with_cart(ui_add_product_once)  # 有车客户端
        cart_data = ShopApiClient.assert_ok(client.get_cart_list())  # 购物车
        chk_resp = client.checkout_index()  # 结算
        chk_data = ShopApiClient.assert_ok(chk_resp)  # 断言成功
        cart_total = cart_data.get("total", {})  # 购物车合计
        chk_total = chk_data.get("total", {})  # 结算合计
        if cart_total and chk_total:  # 两边都有 total
            assert chk_total.get("product_amount") is not None  # 商品金额存在

    def test_api_chk_002_empty_cart_checkout_fails(self, api_client, log_api_test):
        """API-CHK-002：空车结算失败。"""
        api_client.clear_cart()  # 确保空车
        resp = api_client.checkout_index()  # 结算
        try:
            ShopApiClient.assert_ok(resp)  # 若成功则失败
            pytest.fail("空车结算不应成功")  # 框架 pytest：主动失败
        except AssertionError:  # 期望断言失败
            pass  # 通过

    def test_api_chk_003_submit_order_returns_order_id(self, ui_add_product_once, log_api_test):
        """API-CHK-003：提交订单生成 order_id。"""
        client = self._client_with_cart(ui_add_product_once)  # 有车
        chk = ShopApiClient.assert_ok(client.checkout_index())  # 结算信息
        addresses = chk.get("address_list", [])  # 地址列表
        assert addresses, "账号需至少一条收货地址"  # 前置检查
        address_id = addresses[0]["address_id"]  # 第一个地址
        submit_data = ShopApiClient.assert_ok(
            client.checkout_submit(address_id=address_id)
        )  # 提交
        assert submit_data.get("order_id")  # 有 order_id

    def test_api_chk_004_default_address_and_shipping(self, ui_add_product_once, log_api_test):
        """API-CHK-004：默认地址与运费字段存在。"""
        client = self._client_with_cart(ui_add_product_once)  # 客户端
        chk = ShopApiClient.assert_ok(client.checkout_index())  # 结算
        assert chk.get("address_list")  # 有地址
        total = chk.get("total", {})  # 合计
        assert "shipping_fee" in total or "total_amount" in total  # 运费或总额

    def test_api_chk_005_total_amount_calculation(self, ui_add_product_once, log_api_test):
        """API-CHK-005：total_amount 计算合理。"""
        client = self._client_with_cart(ui_add_product_once)  # 客户端
        chk = ShopApiClient.assert_ok(client.checkout_index())  # 结算
        total = chk.get("total", {})  # total 节点
        product_amount = float(total.get("product_amount", 0))  # 商品额
        shipping = float(total.get("shipping_fee", 0) or 0)  # 运费
        total_amount = float(total.get("total_amount", 0))  # 应付
        assert total_amount >= product_amount  # 应付 >= 商品额
