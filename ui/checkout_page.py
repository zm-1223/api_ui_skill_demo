"""结算页 POM：/order/check，封装金额展示、提交订单、价格变动弹窗。"""
import logging  # 框架标准库：日志

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from ui.base_page import BasePage  # 自定义调用：基类

logger = logging.getLogger("tigshop_test.page.checkout")  # logger


class CheckoutPage(BasePage):
    """订单结算页面对象。"""

    PATH = "/order/check"  # 结算页路由

    _SUBMIT_BTN = (By.XPATH, "//button[contains(.,'提交订单')]")  # 提交订单
    _AMOUNT_AREA = (By.XPATH, "//*[contains(text(),'应付') or contains(text(),'实付')]")  # 应付金额
    _SHIPPING_AREA = (By.XPATH, "//*[contains(text(),'运费')]")  # 运费展示
    _PRODUCT_NAME = (By.CSS_SELECTOR, ".product-name, .goods-name, [class*='product']")  # 商品名

    def open_checkout(self) -> "CheckoutPage":
        """直接打开结算页（通常从购物车跳转）。"""
        self.open(self.PATH)  # 导航
        logger.info("打开结算页")  # 日志
        return self  # 链式

    def has_product_displayed(self) -> bool:
        """结算页是否展示商品信息。"""
        body = self.page_text()  # 页面全文
        return "商品" in body or "合计" in body or "应付" in body  # 关键字判断

    def get_payable_text(self) -> str:
        """读取应付/实付金额区域文本。"""
        try:
            return self.wait.present(self._AMOUNT_AREA).text  # 等待并取文本
        except Exception:  # 未找到专用元素
            return self.page_text()  # 全文兜底

    def get_shipping_text(self) -> str:
        """读取运费相关文本。"""
        try:
            return self.wait.present(self._SHIPPING_AREA).text  # 运费元素
        except Exception:
            return ""  # 无运费元素

    def submit_order(self) -> "CheckoutPage":
        """点击提交订单，并处理可能出现的价格变动弹窗。"""
        btn = self.wait.clickable(self._SUBMIT_BTN)  # 等待提交按钮
        btn.click()  # 点击提交
        self.popup.confirm_price_change_if_present()  # 自定义：局部处理变价弹窗
        logger.info("已提交订单，当前 URL: %s", self.current_url())  # 日志
        return self  # 链式

    def is_on_payment_page(self) -> bool:
        """是否已跳转到支付页（URL 含 pay）。"""
        return "pay" in self.current_url().lower()  # URL 判断
