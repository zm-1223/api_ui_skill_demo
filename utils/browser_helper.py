"""浏览器驱动工厂：会话级缓存 ChromeDriver 路径，减少重复 install。"""
import logging  # 框架标准库：日志

from selenium import webdriver  # 框架 Selenium：WebDriver 类型
from selenium.webdriver.chrome.options import Options  # 框架 Selenium：Chrome 选项
from selenium.webdriver.chrome.service import Service  # 框架 Selenium：Chrome 服务
from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动基类
from webdriver_manager.chrome import ChromeDriverManager  # 第三方：自动管理 chromedriver

from config.settings import config  # 自定义调用：headless、等待等配置

logger = logging.getLogger("tigshop_test.browser")  # 浏览器模块 logger

# 进程内缓存：同一次 pytest 会话只 resolve 一次 chromedriver 路径
_CACHED_DRIVER_PATH: str | None = None  # 自定义：模块级路径缓存


class BrowserHelper:
    """集中创建 Chrome WebDriver，供 e2e/api fixture 复用。"""

    @classmethod
    def chromedriver_path(cls) -> str:
        """返回 chromedriver 可执行路径（会话内只 install 一次）。"""
        global _CACHED_DRIVER_PATH  # 自定义：引用模块级缓存
        if _CACHED_DRIVER_PATH is None:  # 首次调用
            _CACHED_DRIVER_PATH = ChromeDriverManager().install()  # 第三方：下载/定位 driver
            logger.info("ChromeDriver 路径已缓存: %s", _CACHED_DRIVER_PATH)  # 日志
        return _CACHED_DRIVER_PATH  # 返回缓存路径

    @classmethod
    def chrome_service(cls) -> Service:
        """基于缓存路径构造 Selenium Service。"""
        return Service(cls.chromedriver_path())  # 框架 Selenium：Service 实例

    @classmethod
    def chrome_options(cls) -> Options:
        """读取 config 构造 Chrome Options。"""
        opts = Options()  # 框架 Selenium：选项对象
        if config.headless:  # 自定义配置：无头模式
            opts.add_argument("--headless=new")  # Chromium headless
        opts.add_argument("--window-size=1400,900")  # 固定窗口大小
        opts.add_argument("--disable-gpu")  # Windows 稳定性
        return opts  # 返回选项

    @classmethod
    def create_chrome(cls) -> WebDriver:
        """启动 Chrome 并设置隐性等待。"""
        driver = webdriver.Chrome(
            service=cls.chrome_service(), options=cls.chrome_options()
        )  # 框架 Selenium：启动浏览器
        driver.implicitly_wait(config.implicit_wait)  # 框架：隐性等待
        logger.info("Chrome WebDriver 已创建")  # 日志
        return driver  # 返回驱动实例
