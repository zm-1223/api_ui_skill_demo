"""登录 API 用例：API-AUTH-001 ~ 003。"""
import pytest  # 框架 pytest：标记与用例

from api.shop_api_client import ShopApiClient  # 自定义：API 客户端
from config.settings import config  # 自定义：账号配置


@pytest.mark.api  # 框架 pytest：api 标记
@pytest.mark.auth  # 框架 pytest：auth 模块标记
class TestAuthApi:
    """登录接口测试类。"""

    def test_api_auth_001_login_success_returns_token(self, shared_access_token, log_api_test):
        """API-AUTH-001：会话共享 token 可用且通过接口校验。"""
        assert shared_access_token  # token 非空
        assert len(shared_access_token) > 20  # JWT 长度合理
        client = ShopApiClient(token=shared_access_token)  # 带 token 客户端
        data = ShopApiClient.assert_ok(client.get_cart_count())  # 鉴权接口可通
        assert "count" in data  # 返回含 count 字段

    def test_api_auth_002_wrong_password_fails(self, log_api_test):
        """API-AUTH-002：错误密码 API 登录业务失败。"""
        client = ShopApiClient()  # 无 token 客户端
        body = client.login(password=config.wrong_password)  # 错误密码登录
        assert body.get("code") != 0  # 业务失败

    def test_api_auth_003_cart_without_token_returns_401(self, api_client_raw, log_api_test):
        """API-AUTH-003：未登录访问购物车返回 401 或业务未授权。"""
        resp = api_client_raw.get_cart_list()  # 无 token 拉列表
        body = resp.json()  # 解析 JSON
        assert body.get("code") in (401, 1001, 1002, 403) or resp.status_code == 401  # 未授权
