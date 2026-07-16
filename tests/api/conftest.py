"""API 层 pytest fixtures：复用会话 token，仅清购物车不重复登录。"""
import logging  # 框架标准库

import pytest  # 框架 pytest：fixture 装饰器

from api.auth_helper import AuthHelper  # 自定义：鉴权
from api.shop_api_client import ShopApiClient  # 自定义：API 客户端

logger = logging.getLogger("tigshop_test.api.fixture")  # API fixture 日志


@pytest.fixture  # 框架 pytest：无鉴权客户端
def api_client_raw():
    """未登录的 API 客户端，用于 API-AUTH-003 等。"""
    return ShopApiClient()  # 无 token


@pytest.fixture  # 框架 pytest：带 token 客户端
def api_client(shared_access_token):
    """已登录客户端；使用会话共享 token，setup/teardown 清空购物车。"""
    client = ShopApiClient(token=shared_access_token)  # 注入共享 token
    client.clear_cart()  # setup：清空购物车
    yield client  # 交给用例
    client.clear_cart()  # teardown：清空购物车
    logger.info("api_client fixture 清理完成")  # 日志


@pytest.fixture  # 框架 pytest：日志用例名
def log_api_test(request):
    """记录当前 API 用例名称。"""
    logger.info("开始 API 用例: %s", request.node.name)  # 用例名
    yield  # 执行用例
    logger.info("结束 API 用例: %s", request.node.name)  # 结束


@pytest.fixture  # 框架 pytest：UI 加购辅助
def ui_add_product_once(shared_access_token):
    """注入 token 后 UI 加购一件商品，返回 token 供 API 断言。"""
    from selenium import webdriver  # 框架 Selenium
    from selenium.webdriver.chrome.options import Options  # Chrome 选项
    from selenium.webdriver.chrome.service import Service  # Chrome 服务
    from webdriver_manager.chrome import ChromeDriverManager  # 第三方 driver

    from config.settings import config  # 配置
    from ui.product_page import ProductPage  # 自定义 POM

    opts = Options()  # Chrome 配置
    if config.headless:
        opts.add_argument("--headless=new")  # 无头
    opts.add_argument("--window-size=1400,900")  # 窗口
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )  # 启动浏览器
    driver.implicitly_wait(config.implicit_wait)  # 隐性等待
    try:
        AuthHelper.inject_token_to_driver(driver, shared_access_token)  # 注入 Cookie，跳过登录
        ProductPage(driver).open_product().add_to_cart(1)  # 加购 1 件
        yield shared_access_token  # 返回共享 token
    finally:
        driver.quit()  # 关闭浏览器
