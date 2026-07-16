"""API 层 pytest fixtures：module 级 UI 浏览器复用；token 会话共享。"""
import logging  # 框架标准库

import pytest  # 框架 pytest：fixture 装饰器
from selenium.webdriver.remote.webdriver import WebDriver  # 框架 Selenium：驱动类型

from api.auth_helper import AuthHelper  # 自定义：鉴权
from api.shop_api_client import ShopApiClient  # 自定义：API 客户端
from ui.product_page import ProductPage  # 自定义 POM：商品页加购
from utils.browser_helper import BrowserHelper  # 自定义：浏览器工厂

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


@pytest.fixture(scope="module")  # 框架 pytest：同文件共用浏览器
def ui_browser(shared_access_token) -> WebDriver:
    """module 级 Chrome：test_cart_api / test_checkout_api / test_payment_api 各启一次。"""
    driver = BrowserHelper.create_chrome()  # 自定义：启动 Chrome
    AuthHelper.inject_token_to_driver(driver, shared_access_token)  # 自定义：注入 token
    yield driver  # 交给 module 内 ui_add_product_once
    logger.info("module 级 ui_browser 关闭")  # 日志
    driver.quit()  # 框架 Selenium：关闭


@pytest.fixture  # 框架 pytest：每条用例 function 级加购（复用 ui_browser）
def ui_add_product_once(ui_browser, shared_access_token):
    """
    在 module 共享浏览器上 UI 加购 1 件；每条用例前 API clear 保证隔离。
    浏览器只开 3 次（cart/checkout/payment 三个 module），不再每条用例冷启动。
    """
    client = ShopApiClient(token=shared_access_token)  # 自定义：API 客户端
    client.clear_cart()  # setup：API 清车，避免 module 内前序用例污染
    ProductPage(ui_browser).open_product().add_to_cart(1)  # 自定义 POM：UI 加购
    yield shared_access_token  # 返回 token 供 ShopApiClient 构造
    client.clear_cart()  # teardown：清车，便于下一条用例
