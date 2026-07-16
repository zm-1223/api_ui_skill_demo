# ui 包初始化：POM 页面对象层，封装元素定位与页面操作
from ui.base_page import BasePage  # 自定义调用：Page 基类
from ui.login_page import LoginPage  # 自定义调用：登录页
from ui.product_page import ProductPage  # 自定义调用：商品详情页
from ui.cart_page import CartPage  # 自定义调用：购物车页
from ui.checkout_page import CheckoutPage  # 自定义调用：结算页
from ui.payment_page import PaymentPage  # 自定义调用：支付页
from ui.order_page import OrderPage  # 自定义调用：订单列表页

__all__ = [
    "BasePage",
    "LoginPage",
    "ProductPage",
    "CartPage",
    "CheckoutPage",
    "PaymentPage",
    "OrderPage",
]
