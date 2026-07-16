"""登录 UI 用例：AUTH-001 ~ 002（POM，test 层不写 locator）。"""
import pytest  # 框架 pytest

from config.settings import config  # 自定义配置
from ui.login_page import LoginPage  # 自定义 POM
from utils.browser_helper import BrowserHelper  # 自定义：浏览器工厂


@pytest.fixture(scope="function")  # 框架 pytest：登录用例需独立浏览器，覆盖 e2e/conftest class 级 driver
def driver():
    """
    登录专项用例使用 function 级 driver。
    避免 AUTH-001 登录成功后 AUTH-002 共用同一 session 导致断言失真。
    """
    drv = BrowserHelper.create_chrome()  # 自定义：启动 Chrome
    yield drv  # 交给用例
    drv.quit()  # 框架 Selenium：关闭


@pytest.mark.ui  # UI 标记
@pytest.mark.auth  # 登录模块
class TestAuthUi:
    """登录 UI 测试。"""

    def test_auth_001_login_success_goes_member_area(self, driver, log_test_name):
        """AUTH-001：正确登录后离开登录页。"""
        page = LoginPage(driver)  # POM 实例
        page.login(config.username, config.password).wait_login_success()  # 登录流程
        assert not page.is_still_on_login()  # 不在登录页
        assert "login" not in page.current_url().lower()  # URL 不含 login

    def test_auth_002_wrong_password_stays_on_login(self, driver, log_test_name):
        """AUTH-002：错误密码仍停留登录页或出现错误提示。"""
        page = LoginPage(driver)  # POM
        page.login(config.username, config.wrong_password)  # 错误密码
        still_login = page.is_still_on_login()  # 是否仍在登录页
        err = page.get_error_message()  # 错误文案
        assert still_login or err  # 停留或报错
