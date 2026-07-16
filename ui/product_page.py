"""商品详情页 POM：/item/{product_sn}，封装加购与角标读取。"""
import logging  # 框架标准库：日志
import re  # 框架标准库：正则提取数字

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from config.settings import config  # 自定义调用：商品 SN、路径
from ui.base_page import BasePage  # 自定义调用：基类

logger = logging.getLogger("tigshop_test.page.product")  # Page logger


class ProductPage(BasePage):
    """商品详情页：加购、读角标、跳转购物车。"""

    PATH = "/item/"  # 前缀，实际需拼 SN

    _ADD_CART_BTN = (By.XPATH, "//button[contains(.,'加入购物车')]")  # 加购按钮
    _BUY_NOW_BTN = (By.XPATH, "//button[contains(.,'立即购买')]")  # 立即购买
    _CART_BADGE_AREA = (By.XPATH, "//*[contains(text(),'购物车')]")  # 角标区域

    def open_product(self, product_sn: str | None = None) -> "ProductPage":
        """打开指定 SN 的商品详情页。"""
        path = config.product_path(product_sn)  # 自定义：/item/SN0000548
        self.open(path)  # 基类导航
        self.popup.dismiss_cookie_if_present()  # 自定义：按需关 Cookie 弹窗
        logger.info("打开商品页: %s", path)  # 日志
        return self  # 链式

    def add_to_cart(self, quantity: int = 1) -> "ProductPage":
        """点击加入购物车；quantity>1 时重复点击（无规格商品）。"""
        for _ in range(quantity):  # 自定义：重复加购实现数量
            btn = self.wait.clickable(self._ADD_CART_BTN)  # 等待加购按钮
            btn.click()  # 框架：点击
            logger.info("点击加入购物车")  # 日志
        self.popup.dismiss_overlay_if_present()  # 按需关遮罩
        return self  # 链式

    def get_badge_count(self) -> str:
        """从头部购物车区域提取角标数字，无商品返回 '0'。"""
        try:
            el = self.wait.present(self._CART_BADGE_AREA)  # 等待购物车文案区域
            text = el.text  # 可能含「我的购物车\n2」
            nums = re.findall(r"\d+", text)  # 正则提取数字
            return nums[-1] if nums else "0"  # 取最后一个数字为角标
        except Exception:  # 未找到元素
            return "0"  # 默认 0

    def go_cart(self) -> "ProductPage":
        """点击头部购物车入口。"""
        el = self.wait.clickable(self._CART_BADGE_AREA)  # 购物车链接
        el.click()  # 点击跳转
        logger.info("跳转购物车")  # 日志
        return self  # 链式
