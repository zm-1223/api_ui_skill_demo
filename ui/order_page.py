"""订单列表页 POM：/member/order/list，封装订单状态读取。"""
import logging  # 框架标准库：日志

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from config.settings import config  # 自定义：状态文案
from ui.base_page import BasePage  # 自定义：基类

logger = logging.getLogger("tigshop_test.page.order")  # logger


class OrderPage(BasePage):
    """会员订单列表页面对象。"""

    PATH = "/member/order/list"  # 订单列表路由

    _ORDER_ITEM = (By.CSS_SELECTOR, ".order-item, [class*='order-list'], .el-table__row")  # 订单行
    _STATUS = (By.XPATH, "//*[contains(text(),'待支付') or contains(text(),'已支付')]")  # 状态文案

    def open_order_list(self) -> "OrderPage":
        """打开我的订单列表。"""
        self.open(self.PATH)  # 导航
        logger.info("打开订单列表")  # 日志
        return self  # 链式

    def get_page_status_text(self) -> str:
        """返回页面中与订单状态相关的可见文本。"""
        return self.page_text()  # 全文供 test 断言

    def has_pending_order(self) -> bool:
        """列表中是否存在待支付订单。"""
        text = self.page_text()  # 读全文
        return config.expected_pending_status in text or "待支付" in text  # 判断

    def has_paid_order(self) -> bool:
        """列表中是否存在已支付订单。"""
        text = self.page_text()  # 读全文
        return config.expected_paid_status in text or "已支付" in text  # 判断

    def wait_orders_loaded(self) -> "OrderPage":
        """等待订单列表区域加载（表格或列表项）。"""
        try:
            self.wait.present(self._ORDER_ITEM)  # 等待订单行
        except Exception:  # 无专用 class 则等待状态文案
            self.wait.present(self._STATUS)  # 等待状态文字
        logger.info("订单列表已加载")  # 日志
        return self  # 链式
