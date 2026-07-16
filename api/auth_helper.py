"""登录态辅助：优先复用缓存 token，必要时才 UI 登录。"""
import logging  # 框架标准库：日志

from selenium.webdriver.common.by import By  # 框架 Selenium：定位

from config.settings import config  # 自定义调用：全局配置
from utils.token_store import TokenStore  # 自定义调用：Token 复用
from utils.wait_helper import WaitHelper  # 自定义调用：显式等待
from utils.browser_helper import BrowserHelper  # 自定义调用：浏览器工厂

logger = logging.getLogger("tigshop_test.auth")  # 框架 logging：鉴权 logger


class AuthHelper:
    """提供 Token 复用、UI 登录、Cookie 注入等鉴权能力。"""

    @staticmethod
    def get_token(*, force_refresh: bool = False) -> str:
        """获取可用 accessToken（优先缓存，避免重复登录）。"""
        return TokenStore.resolve(force_refresh=force_refresh)  # 自定义调用：TokenStore

    @staticmethod
    def login_via_ui(headless: bool | None = None) -> str:
        """通过 Selenium UI 登录（仅 fallback 或首次录入 token 时使用）。"""
        _ = headless  # 保留参数兼容；headless 由 config + BrowserHelper 控制
        driver = BrowserHelper.create_chrome()  # 自定义：复用缓存 chromedriver 路径
        wait = WaitHelper(driver)  # 显式等待（默认 2s 用于元素）
        login_wait = config.login_wait_sec  # 登录专用更长等待
        try:
            driver.get(f"{config.base_url}{config.login_url}")  # 打开登录页
            wait.clickable((By.CSS_SELECTOR, ".el-checkbox__input")).click()  # 勾选协议
            inputs = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")  # 输入框
            inputs[0].clear()  # 清空用户名
            inputs[0].send_keys(config.username)  # 输入用户名
            inputs[1].clear()  # 清空密码
            inputs[1].send_keys(config.password)  # 输入密码
            wait.clickable((By.CSS_SELECTOR, "button.login_btn")).click()  # 点击登录

            def _has_token(drv):  # 轮询：是否已有 accessToken
                return drv.get_cookie(config.token_cookie) is not None  # Cookie 存在

            from selenium.webdriver.support.ui import WebDriverWait  # 框架：长等待

            WebDriverWait(driver, login_wait).until(_has_token)  # 登录专用 15s
            cookie = driver.get_cookie(config.token_cookie)  # 读取 Cookie
            if not cookie:  # 仍未拿到
                raise RuntimeError("UI 登录未获取到 accessToken（可能需手动完成滑块）")  # 异常
            token = cookie["value"]  # 提取 token
            TokenStore.save_to_file(token)  # 自定义：落盘供下次复用
            logger.info("UI 登录成功，token 长度=%s", len(token))  # 日志
            return token  # 返回
        finally:
            driver.quit()  # 关闭浏览器

    @staticmethod
    def apply_token(session, token: str) -> None:
        """将 token 写入 requests.Session 的 Cookie 与 Authorization 头。"""
        session.cookies.set(config.token_cookie, token, domain="demo.tigshop.cn")  # Cookie
        session.headers[config.token_header] = f"{config.token_prefix}{token}"  # Header

    @staticmethod
    def inject_token_to_driver(driver, token: str | None = None) -> None:
        """向已打开的 WebDriver 注入 accessToken Cookie，跳过登录页与滑块。"""
        token = token or AuthHelper.get_token()  # 未传则取缓存 token
        driver.get(config.base_url)  # 必须先访问同域页面才能 add_cookie
        driver.add_cookie(
            {
                "name": config.token_cookie,  # accessToken
                "value": token,  # JWT 字符串
                "domain": "demo.tigshop.cn",  # 站点域
                "path": "/",  # 全站有效
            }
        )  # 框架 Selenium：注入 Cookie
        driver.refresh()  # 刷新使登录态生效
        logger.info("已向浏览器注入 accessToken Cookie")  # 日志
