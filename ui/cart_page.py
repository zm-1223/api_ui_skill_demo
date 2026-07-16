"""购物车页 POM：/cart，封装空态、删除、结算、金额读取。"""
import logging  # 框架标准库：日志
import re  # 框架标准库：正则

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from ui.base_page import BasePage  # 自定义调用：基类

logger = logging.getLogger("tigshop_test.page.cart")  # logger


class CartPage(BasePage):
    """购物车列表页面对象。"""

    PATH = "/cart"  # 购物车路由

    _EMPTY_HINT = (By.XPATH, "//*[contains(text(),'购物车为空') or contains(text(),'暂无')]")  # 空态
    _DELETE_BTN = (By.XPATH, "//button[contains(.,'删除')]")  # 删除按钮
    _CHECKOUT_BTN = (By.XPATH, "//button[contains(.,'结算') or contains(.,'去结算')]")  # 去结算
    _TOTAL_AREA = (By.XPATH, "//*[contains(text(),'合计') or contains(text(),'总计')]")  # 合计区域

    def open_cart(self) -> "CartPage":
        """打开购物车页。"""
        self.open(self.PATH)  # 基类 open
        logger.info("打开购物车页")  # 日志
        return self  # 链式

    def is_empty_cart_displayed(self) -> bool:
        """页面是否展示空购物车文案。"""
        try:
            self.wait.present(self._EMPTY_HINT)  # 等待空态文案
            return True  # 找到即空车
        except Exception:  # 超时未找到
            body = self.page_text()  # 读全文兜底
            return "购物车为空" in body or "暂无" in body  # 文本判断

    def delete_first_item(self) -> "CartPage":
        """删除第一条购物车商品。"""
        btn = self.wait.clickable(self._DELETE_BTN)  # 等待删除按钮
        btn.click()  # 点击删除
        logger.info("删除购物车第一条商品")  # 日志
        return self  # 链式

    def go_checkout(self) -> "CartPage":
        """点击去结算。"""
        btn = self.wait.clickable(self._CHECKOUT_BTN)  # 结算按钮
        btn.click()  # 点击
        logger.info("点击去结算")  # 日志
        return self  # 链式

    def get_total_amount_text(self) -> str:
        """读取合计金额区域文本。"""
        try:
            el = self.wait.present(self._TOTAL_AREA)  # 合计元素
            return el.text  # 返回文本
        except Exception:  # 未找到
            return self.page_text()  # 兜底全文

    def extract_amount_number(self, text: str) -> float | None:
        """从文本中提取金额数字（如 ￥11.00 -> 11.0）。"""
        matches = re.findall(r"\d+\.?\d*", text)  # 正则数字
        if not matches:  # 无数字
            return None  # 返回 None
        return float(matches[-1])  # 取最后一个作为合计
