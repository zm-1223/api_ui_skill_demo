"""显式等待封装：禁止 sleep，统一 WebDriverWait + EC。"""
from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动类型
from selenium.webdriver.support import expected_conditions as EC  # 框架 Selenium：期望条件
from selenium.webdriver.support.ui import WebDriverWait  # 框架 Selenium：显式等待

from config.settings import config  # 自定义调用：读取 explicit_wait 配置


class WaitHelper:
    """对 WebDriverWait 的薄封装，供 Page 与 Helper 使用。"""

    def __init__(self, driver: WebDriver) -> None:
        """保存 driver 并创建 WebDriverWait 实例。"""
        self.driver = driver  # 自定义：保存浏览器驱动引用
        self.timeout = config.explicit_wait  # 自定义：从配置读取超时秒数
        self.wait = WebDriverWait(driver, self.timeout)  # 框架：创建显式等待对象

    def visible(self, locator: tuple) -> object:
        """等待元素可见并返回该元素。"""
        return self.wait.until(EC.visibility_of_element_located(locator))  # 框架 EC：可见

    def clickable(self, locator: tuple) -> object:
        """等待元素可点击并返回该元素。"""
        return self.wait.until(EC.element_to_be_clickable(locator))  # 框架 EC：可点击

    def present(self, locator: tuple) -> object:
        """等待元素存在于 DOM 并返回该元素。"""
        return self.wait.until(EC.presence_of_element_located(locator))  # 框架 EC：存在

    def text_in_element(self, locator: tuple, text: str) -> bool:
        """等待元素文本包含指定子串。"""
        return self.wait.until(EC.text_to_be_present_in_element(locator, text))  # 框架 EC：文本

    def url_contains(self, fragment: str) -> bool:
        """等待当前 URL 包含指定片段。"""
        return self.wait.until(EC.url_contains(fragment))  # 框架 EC：URL 包含

    def invisible(self, locator: tuple) -> bool:
        """等待元素不可见或从 DOM 移除。"""
        return self.wait.until(EC.invisibility_of_element_located(locator))  # 框架 EC：不可见
