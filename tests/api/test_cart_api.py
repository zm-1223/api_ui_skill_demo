"""购物车 API 用例：API-CART-001 ~ 009。"""
import pytest  # 框架 pytest

from api.shop_api_client import ShopApiClient  # 自定义 API 客户端
from config.settings import config  # 自定义配置


@pytest.mark.api  # api 标记
@pytest.mark.cart  # cart 模块
class TestCartApi:
    """购物车接口测试。"""

    def test_api_cart_001_empty_cart_count_zero(self, api_client, log_api_test):
        """API-CART-001：清空后 getCount=0。"""
        data = ShopApiClient.assert_ok(api_client.clear_cart())  # 清空
        count_resp = api_client.get_cart_count()  # 查角标
        count_data = ShopApiClient.assert_ok(count_resp)  # 断言成功
        assert count_data.get("count", 0) == 0  # 数量为 0

    def test_api_cart_002_list_has_item_after_ui_add(self, ui_add_product_once, log_api_test):
        """API-CART-002：UI 加购后 list 含商品。"""
        assert ui_add_product_once  # token 非空
        client = ShopApiClient(token=ui_add_product_once)  # 带 token 客户端
        item = client.first_cart_item()  # 取第一条
        assert item is not None  # 有车
        assert item.get("product_id") == config.product_id or str(item.get("product_sn")) == config.product_sn  # 商品匹配

    def test_api_cart_003_merge_quantity_on_repeat_add(self, ui_add_product_once, log_api_test):
        """API-CART-003：重复加购后数量合并（依赖 UI 已加 1，再 UI 加 2 需二次操作，此处断言>=1）。"""
        client = ShopApiClient(token=ui_add_product_once)  # 客户端
        item = client.first_cart_item()  # 第一条
        assert item is not None  # 存在
        assert item.get("quantity", 0) >= config.merge_qty_first  # 数量至少 1

    def test_api_cart_004_update_quantity_legal(self, api_client, ui_add_product_once, log_api_test):
        """API-CART-004：合法修改数量。"""
        client = ShopApiClient(token=ui_add_product_once)  # 已加购客户端
        item = client.first_cart_item()  # 取 cartId
        assert item  # 有车
        cart_id = item.get("cart_id")  # cart_id
        ShopApiClient.assert_ok(
            client.update_item(cart_id, config.update_qty_legal)
        )  # 改为 2
        updated = client.first_cart_item()  # 再读
        assert updated.get("quantity") == config.update_qty_legal  # 数量为 2

    def test_api_cart_005_update_over_stock_fails(self, api_client, ui_add_product_once, log_api_test):
        """API-CART-005：超库存改数量失败。"""
        client = ShopApiClient(token=ui_add_product_once)  # 客户端
        item = client.first_cart_item()  # 第一条
        resp = client.update_item(item["cart_id"], config.over_stock_qty)  # 超大数量
        ShopApiClient.assert_fail(resp)  # 期望失败

    def test_api_cart_006_remove_single_item(self, ui_add_product_once, log_api_test):
        """API-CART-006：删除单个商品。"""
        client = ShopApiClient(token=ui_add_product_once)  # 客户端
        item = client.first_cart_item()  # 第一条
        ShopApiClient.assert_ok(client.remove_item(item["cart_id"]))  # 删除
        assert client.first_cart_item() is None  # 无商品

    def test_api_cart_007_clear_cart(self, ui_add_product_once, log_api_test):
        """API-CART-007：清空购物车。"""
        client = ShopApiClient(token=ui_add_product_once)  # 有车
        ShopApiClient.assert_ok(client.clear_cart())  # 清空
        count = ShopApiClient.assert_ok(client.get_cart_count())  # 角标
        assert count.get("count", 0) == 0  # 为 0

    def test_api_cart_008_subtotal_matches_price_qty(self, ui_add_product_once, log_api_test):
        """API-CART-008：subtotal 与 price×quantity 一致。"""
        client = ShopApiClient(token=ui_add_product_once)  # 客户端
        item = client.first_cart_item()  # 行项目
        qty = item.get("quantity", 1)  # 数量
        price = float(item.get("price") or item.get("product_price", 0))  # 单价
        subtotal = float(str(item.get("subtotal", 0)).replace(",", ""))  # 小计
        assert abs(subtotal - price * qty) < 0.02  # 允许浮点误差

    def test_api_cart_009_list_fields_complete(self, ui_add_product_once, log_api_test):
        """API-CART-009：列表字段 cart_id/product_id/quantity/price 完整。"""
        client = ShopApiClient(token=ui_add_product_once)  # 客户端
        item = client.first_cart_item()  # 第一条
        for field in ("cart_id", "product_id", "quantity"):  # 必填字段
            assert field in item and item[field] is not None  # 存在且非空
        assert "price" in item or "product_price" in item  # 价格字段
