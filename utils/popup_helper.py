"""弹窗局部处理：按需关闭 Cookie/协议/价格变动等，禁止 conftest 全局扫描。"""
import logging  # 框架标准库：日志

from selenium.common.exceptions import TimeoutException  # 框架 Selenium：超时异常
from selenium.webdriver.common.by import By  # 框架 Selenium：定位策略
from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动类型
from selenium.webdriver.support import expected_conditions as EC  # 框架 Selenium：期望条件
from selenium.webdriver.support.ui import WebDriverWait  # 框架 Selenium：显式等待

from config.settings import config  # 自定义调用：弹窗等待秒数

logger = logging.getLogger("tigshop_test.popup")  # 框架 logging：弹窗专用 logger


class PopupHelper:
    """在触发步骤后局部调用，处理可能出现的弹窗。"""

    def __init__(self, driver: WebDriver) -> None:
        """保存 driver，弹窗等待使用独立超时（通常 3s）。"""
        self.driver = driver  # 自定义：浏览器驱动
        self.popup_wait = WebDriverWait(driver, config.popup_wait)  # 框架：弹窗专用等待

    def dismiss_cookie_if_present(self) -> None:
        """若存在 Cookie/协议弹窗则点击同意或关闭。"""
        selectors = [
            (By.XPATH, "//button[contains(.,'同意')]"),  # 自定义定位：同意按钮
            (By.XPATH, "//button[contains(.,'接受')]"),  # 自定义定位：接受按钮
            (By.CSS_SELECTOR, ".el-dialog__close"),  # Element UI 关闭图标
        ]
        for locator in selectors:  # 自定义：依次尝试多种关闭方式
            try:
                btn = self.popup_wait.until(EC.element_to_be_clickable(locator))  # 框架 EC
                btn.click()  # 框架 Selenium：点击关闭
                logger.info("已关闭 Cookie/协议弹窗: %s", locator)  # 自定义日志
                return  # 成功则退出
            except TimeoutException:  # 框架异常：该 locator 未出现则继续
                continue  # 尝试下一个 locator

    def confirm_price_change_if_present(self) -> None:
        """提交订单后若出现价格变动确认弹窗则点击确认。"""
        locators = [
            (By.XPATH, "//button[contains(.,'确认')]"),  # 确认按钮
            (By.XPATH, "//button[contains(.,'确定')]"),  # 确定按钮
            (By.CSS_SELECTOR, ".el-message-box__btns .el-button--primary"),  # Element 主按钮
        ]
        for locator in locators:  # 自定义：多 locator 兜底
            try:
                btn = self.popup_wait.until(EC.element_to_be_clickable(locator))  # 框架 EC
                btn.click()  # 框架：点击确认
                logger.info("已确认价格变动弹窗: %s", locator)  # 日志
                return  # 处理完成
            except TimeoutException:  # 未出现则跳过
                continue  # 下一个 locator

    def dismiss_overlay_if_present(self) -> None:
        """关闭通用遮罩层（若阻挡点击）。"""
        try:
            overlay = self.popup_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".el-overlay"))
            )  # 框架 EC：遮罩存在
            if overlay.is_displayed():  # 框架 WebElement：是否显示
                close_btn = self.driver.find_element(By.CSS_SELECTOR, ".el-dialog__close")  # 关闭
                close_btn.click()  # 框架：点击
                logger.info("已关闭遮罩层")  # 日志
        except TimeoutException:  # 无遮罩则忽略
            pass  # 按需局部，不抛异常
