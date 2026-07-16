"""UI fixture：class 级复用浏览器；失败截图；注入共享 token。"""
import logging  # 框架标准库
from datetime import datetime  # 框架标准库

import allure  # 第三方 allure-pytest
import pytest  # 框架 pytest
from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动类型

from api.auth_helper import AuthHelper  # 自定义：Cookie 注入
from api.shop_api_client import ShopApiClient  # 自定义：API 清购物车
from config.settings import config  # 自定义配置
from utils.browser_helper import BrowserHelper  # 自定义：浏览器工厂

logger = logging.getLogger("tigshop_test.ui.fixture")  # UI fixture 日志


@pytest.fixture(scope="class")  # 框架 pytest：同一 TestClass 共用浏览器
def driver(request) -> WebDriver:
    """创建 Chrome；class 结束时关闭，同 class 内用例共享实例。"""
    drv = BrowserHelper.create_chrome()  # 自定义：缓存 driver 路径后启动
    yield drv  # 交给 class 内各用例
    logger.info("class 级 driver 关闭: %s", request.cls.__name__)  # 日志
    drv.quit()  # 框架 Selenium：关闭浏览器


@pytest.fixture(autouse=True)  # 框架 pytest：每条 UI 用例自动执行
def _ui_failure_screenshot(request) -> None:
    """function 级：用例失败时对当前 class 共享 driver 截图并 attach Allure。"""
    yield  # 先执行用例
    rep = getattr(request.node, "rep_call", None)  # 读取 call 阶段报告
    if rep is None or not rep.failed:  # 未失败则跳过
        return  # 不截图
    if "driver" not in request.fixturenames and "logged_in_driver" not in request.fixturenames:
        return  # 非浏览器用例
    try:
        drv = (
            request.getfixturevalue("driver")
            if "driver" in request.fixturenames
            else request.getfixturevalue("logged_in_driver")
        )  # 框架 pytest：取已缓存的 class 级 driver
    except Exception as exc:  # fixture 不可用
        logger.warning("失败截图跳过（无 driver）: %s", exc)  # 日志
        return  # 跳过
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 时间戳
    path = (
        config.ROOT_DIR / "reports" / "screenshots" / f"{request.node.name}_{ts}.png"
    )  # 截图路径
    try:
        drv.save_screenshot(str(path))  # 框架 Selenium：保存 PNG
        logger.error("用例失败截图: %s", path)  # 日志
        with open(path, "rb") as f:  # 读二进制
            allure.attach(
                f.read(),
                name=f"失败截图_{request.node.name}",
                attachment_type=allure.attachment_type.PNG,
            )  # 第三方 allure：附加到报告
    except Exception as exc:  # 截图失败
        logger.error("截图/Allure附加失败: %s", exc)  # 记录


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # 框架 pytest：钩子
def pytest_runtest_makereport(item, call):  # 记录用例执行结果
    """保存 rep_call 到 item，供 _ui_failure_screenshot 判断失败。"""
    outcome = yield  # 框架 hookwrapper
    rep = outcome.get_result()  # 获取报告
    setattr(item, f"rep_{rep.when}", rep)  # 挂到 item


@pytest.fixture(scope="class")  # 框架 pytest：同 class 只注入一次 token
def logged_in_driver(driver, shared_access_token) -> WebDriver:
    """向 class 共享 driver 注入 accessToken；跳过登录页与滑块。"""
    AuthHelper.inject_token_to_driver(driver, shared_access_token)  # 自定义：Cookie 注入
    yield driver  # 返回已登录驱动
    logger.info("logged_in_driver class 结束: %s", driver)  # 日志


@pytest.fixture(autouse=True)  # 框架 pytest：每条 UI 用例前执行
def _reset_cart_before_ui_test(shared_access_token, request) -> None:
    """API 清空购物车，避免 class 内用例互相污染（仅 @pytest.mark.ui 用例）。"""
    if request.node.get_closest_marker("ui") is None:  # 非 UI 用例
        yield  # 不干预
        return  # 结束
    client = ShopApiClient(token=shared_access_token)  # 自定义：API 客户端
    client.clear_cart()  # 自定义：POST clear
    logger.info("UI 用例前已 clear_cart: %s", request.node.name)  # 日志
    yield  # 执行用例


@pytest.fixture  # 记录用例名
def log_test_name(request):
    """UI 用例开始/结束日志。"""
    logger.info("开始 UI 用例: %s", request.node.name)  # 开始
    yield  # 执行
    logger.info("结束 UI 用例: %s", request.node.name)  # 结束
