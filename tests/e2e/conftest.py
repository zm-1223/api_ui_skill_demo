"""UI fixture：注入共享 token；失败截图附加到 Allure。"""
import logging  # 框架标准库
from datetime import datetime  # 框架标准库

import allure  # 第三方 allure-pytest
import pytest  # 框架 pytest
from selenium import webdriver  # 框架 Selenium
from selenium.webdriver.chrome.options import Options  # Chrome 选项
from selenium.webdriver.chrome.service import Service  # Chrome 服务
from webdriver_manager.chrome import ChromeDriverManager  # 第三方

from api.auth_helper import AuthHelper  # 自定义：Cookie 注入
from config.settings import config  # 自定义配置

logger = logging.getLogger("tigshop_test.ui.fixture")  # UI fixture 日志


@pytest.fixture  # 框架 pytest：浏览器驱动
def driver(request):
    """创建 Chrome WebDriver；失败时截图并 attach 到 Allure。"""
    opts = Options()  # Chrome 选项
    if config.headless:  # 无头配置
        opts.add_argument("--headless=new")  # headless
    opts.add_argument("--window-size=1400,900")  # 窗口大小
    opts.add_argument("--disable-gpu")  # 稳定性
    drv = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )  # 启动 Chrome
    drv.implicitly_wait(config.implicit_wait)  # 隐性等待
    yield drv  # 交给用例
    failed = (
        hasattr(request.node, "rep_call") and request.node.rep_call.failed
    )  # 判断是否失败
    if failed:  # 失败则截图
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 时间戳
        path = (
            config.ROOT_DIR / "reports" / "screenshots" / f"{request.node.name}_{ts}.png"
        )  # 截图路径
        try:
            drv.save_screenshot(str(path))  # 保存 PNG
            logger.error("用例失败截图: %s", path)  # 日志
            with open(path, "rb") as f:  # 读二进制
                allure.attach(
                    f.read(),
                    name=f"失败截图_{request.node.name}",
                    attachment_type=allure.attachment_type.PNG,
                )  # 附加到 Allure
        except Exception as exc:  # 截图失败
            logger.error("截图/Allure附加失败: %s", exc)  # 记录
    drv.quit()  # 关闭浏览器


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # 框架 pytest：钩子
def pytest_runtest_makereport(item, call):  # 记录用例执行结果
    """保存 rep_call 到 item 供 driver fixture 判断失败。"""
    outcome = yield  # 框架 hookwrapper
    rep = outcome.get_result()  # 获取报告
    setattr(item, f"rep_{rep.when}", rep)  # 挂到 item


@pytest.fixture  # 已登录 driver（注入 token，不经过登录页）
def logged_in_driver(driver, shared_access_token):
    """向 driver 注入会话共享 accessToken，跳过登录与滑块。"""
    AuthHelper.inject_token_to_driver(driver, shared_access_token)  # Cookie 注入
    yield driver  # 返回已登录驱动
    logger.info("logged_in_driver 用例结束")  # 日志


@pytest.fixture  # 记录用例名
def log_test_name(request):
    """UI 用例开始/结束日志。"""
    logger.info("开始 UI 用例: %s", request.node.name)  # 开始
    yield  # 执行
    logger.info("结束 UI 用例: %s", request.node.name)  # 结束
