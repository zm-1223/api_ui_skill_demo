"""登录页 POM：/member/login，封装协议勾选、登录、错误提示读取。"""
import logging  # 框架标准库：日志

from selenium.webdriver.common.by import By  # 框架 Selenium：定位策略

from ui.base_page import BasePage  # 自定义调用：POM 基类

logger = logging.getLogger("tigshop_test.page.login")  # Page 专用 logger


class LoginPage(BasePage):
    """Tigshop 登录页面对象。"""

    PATH = "/member/login"  # 登录页路由

    # 定位器内聚在 Page 内，不泄露到 test
    _CHECKBOX = (By.CSS_SELECTOR, ".el-checkbox__input")  # 协议勾选框
    _INPUTS = (By.CSS_SELECTOR, "input.el-input__inner")  # 用户名/密码输入框
    _LOGIN_BTN = (By.CSS_SELECTOR, "button.login_btn")  # 登录按钮
    _ERROR = (By.CSS_SELECTOR, ".el-form-item__error, .el-message__content")  # 错误提示

    def open_login(self) -> "LoginPage":
        """打开登录页并返回 self 链式调用。"""
        self.open(self.PATH)  # 自定义调用：基类 open
        return self  # 链式

    def agree_protocol(self) -> "LoginPage":
        """勾选服务协议与隐私政策。"""
        self.wait.clickable(self._CHECKBOX).click()  # 框架+自定义：等待可点后点击
        logger.info("已勾选登录协议")  # 日志
        return self  # 链式

    def fill_credentials(self, username: str, password: str) -> "LoginPage":
        """填写用户名与密码。"""
        inputs = self.driver.find_elements(*self._INPUTS)  # 框架：查找输入框列表
        inputs[0].clear()  # 框架：清空用户名
        inputs[0].send_keys(username)  # 框架：输入用户名
        inputs[1].clear()  # 框架：清空密码
        inputs[1].send_keys(password)  # 框架：输入密码
        logger.info("已填写登录凭证: %s", username)  # 日志（不记密码）
        return self  # 链式

    def submit(self) -> "LoginPage":
        """点击登录按钮。"""
        self.wait.clickable(self._LOGIN_BTN).click()  # 框架：点击登录
        logger.info("已点击登录按钮")  # 日志
        return self  # 链式

    def login(self, username: str, password: str) -> "LoginPage":
        """完整登录流程：打开 -> 勾选 -> 填表 -> 提交。"""
        return (
            self.open_login()  # 打开页
            .agree_protocol()  # 勾选
            .fill_credentials(username, password)  # 填表
            .submit()  # 提交
        )  # 链式返回

    def wait_login_success(self) -> "LoginPage":
        """等待登录成功：URL 离开 login 或出现 accessToken Cookie（使用 login_wait_sec）。"""
        from config.settings import config  # 自定义：token Cookie 名与登录等待
        from selenium.webdriver.support.ui import WebDriverWait  # 框架：长超时等待

        def _logged_in(drv):  # 自定义：轮询条件函数
            if "/login" not in drv.current_url:  # URL 已离开登录页
                return True  # 成功
            return drv.get_cookie(config.token_cookie) is not None  # 或已有 Cookie

        WebDriverWait(self.driver, config.login_wait_sec).until(_logged_in)  # 登录专用 15s
        logger.info("登录成功，当前 URL: %s", self.current_url())  # 日志
        return self  # 链式

    def get_error_message(self) -> str:
        """读取页面错误提示文本，无则返回空串。"""
        try:
            el = self.wait.present(self._ERROR)  # 框架：等待错误元素
            return el.text.strip()  # 返回文本
        except Exception:  # 无错误元素
            return ""  # 空串

    def is_still_on_login(self) -> bool:
        """是否仍在登录页（用于负向用例）。"""
        return "/login" in self.current_url()  # 自定义：URL 判断
