"""Page 基类：封装 driver、等待、导航，所有 POM 页面继承此类。"""
import logging  # 框架标准库：日志

from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动类型

from config.settings import config  # 自定义调用：base_url 等
from utils.popup_helper import PopupHelper  # 自定义调用：弹窗处理
from utils.wait_helper import WaitHelper  # 自定义调用：显式等待

logger = logging.getLogger("tigshop_test.page")  # 框架 logging：Page 层 logger


class BasePage:
    """POM 基类：提供 open、wait、popup 通用能力，禁止在 test 中直接操作 driver。"""

    PATH = "/"  # 子类覆盖：页面相对路径

    def __init__(self, driver: WebDriver) -> None:
        """注入 driver 并初始化 WaitHelper、PopupHelper。"""
        self.driver = driver  # 自定义：保存 WebDriver 引用
        self.wait = WaitHelper(driver)  # 自定义调用：显式等待封装
        self.popup = PopupHelper(driver)  # 自定义调用：弹窗局部处理

    def open(self, path: str | None = None) -> None:
        """导航到 base_url + path。"""
        target = path if path is not None else self.PATH  # 自定义：默认用类 PATH
        url = f"{config.base_url}{target}"  # 拼接完整 URL
        logger.info("打开页面: %s", url)  # 日志记录
        self.driver.get(url)  # 框架 Selenium：GET 导航

    def current_url(self) -> str:
        """返回当前浏览器 URL。"""
        return self.driver.current_url  # 框架 Selenium：当前 URL

    def page_text(self) -> str:
        """返回 body 可见文本，供 test 层断言。"""
        from selenium.webdriver.common.by import By  # 框架 Selenium：定位（局部导入避免循环）

        return self.driver.find_element(By.TAG_NAME, "body").text  # 框架：取 body 文本
