"""支付页 POM：/order/pay，封装金额展示、取消、支付成功判断。"""
import logging  # 框架标准库：日志

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from config.settings import config  # 自定义：待支付/已支付文案
from ui.base_page import BasePage  # 自定义：基类

logger = logging.getLogger("tigshop_test.page.payment")  # logger


class PaymentPage(BasePage):
    """订单支付页面对象。"""

    PATH = "/order/pay"  # 支付页路径前缀

    _AMOUNT = (By.XPATH, "//*[contains(text(),'支付') or contains(text(),'金额')]")  # 金额区
    _CANCEL_BTN = (By.XPATH, "//button[contains(.,'取消') or contains(.,'返回')]")  # 取消/返回
    _PAY_BTN = (By.XPATH, "//button[contains(.,'支付') or contains(.,'立即支付')]")  # 支付按钮

    def open_payment(self, order_id: int | str | None = None) -> "PaymentPage":
        """打开支付页；可带 order_id 查询参数。"""
        path = self.PATH if order_id is None else f"{self.PATH}?id={order_id}"  # 拼 query
        self.open(path)  # 导航
        logger.info("打开支付页: %s", path)  # 日志
        return self  # 链式

    def get_amount_text(self) -> str:
        """读取支付金额相关文本。"""
        try:
            return self.wait.present(self._AMOUNT).text  # 金额区域
        except Exception:
            return self.page_text()  # 全文

    def cancel_payment(self) -> "PaymentPage":
        """取消支付或返回上一页。"""
        try:
            btn = self.wait.clickable(self._CANCEL_BTN)  # 取消按钮
            btn.click()  # 点击
            logger.info("已取消支付")  # 日志
        except Exception:  # 无取消按钮则浏览器后退
            self.driver.back()  # 框架：后退
            logger.info("使用浏览器后退离开支付页")  # 日志
        return self  # 链式

    def click_pay(self) -> "PaymentPage":
        """点击立即支付（进入第三方支付沙箱，具体流程依赖演示站配置）。"""
        btn = self.wait.clickable(self._PAY_BTN)  # 支付按钮
        btn.click()  # 点击
        logger.info("已点击立即支付")  # 日志
        return self  # 链式

    def is_pending_status_shown(self) -> bool:
        """页面是否展示待支付相关文案。"""
        text = self.page_text()  # 全文
        return config.expected_pending_status in text or "待支付" in text  # 状态判断

    def is_paid_status_shown(self) -> bool:
        """页面是否展示已支付相关文案。"""
        text = self.page_text()  # 全文
        return config.expected_paid_status in text or "已支付" in text or "支付成功" in text  # 判断
