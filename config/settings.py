"""全局配置：从 data/test_data.json 加载站点、账号、等待、商品等参数。"""
import json  # 框架标准库：读取 JSON 配置文件
import os  # 框架标准库：路径拼接
from pathlib import Path  # 框架标准库：跨平台路径对象


class Config:
    """集中管理测试环境配置，供 api/ui/tests 各层引用。"""

    # 项目根目录：当前文件上两级（config -> 根）
    ROOT_DIR = Path(__file__).resolve().parent.parent  # 自定义：定位项目根路径
    DATA_FILE = ROOT_DIR / "data" / "test_data.json"  # 自定义：测试数据 JSON 路径

    @classmethod
    def _load(cls) -> dict:
        """读取 test_data.json 并缓存到类属性。"""
        if not hasattr(cls, "_cache"):  # 自定义：仅首次加载
            with open(cls.DATA_FILE, encoding="utf-8") as f:  # 框架 IO：打开 JSON 文件
                cls._cache = json.load(f)  # 框架 json：解析为 dict
        return cls._cache  # 返回缓存配置

    @classmethod
    def reload(cls) -> None:
        """强制重新加载配置（测试或调试时使用）。"""
        if hasattr(cls, "_cache"):  # 自定义：存在缓存才删除
            delattr(cls, "_cache")  # 框架内置：删除类属性
        cls._load()  # 自定义调用：触发重新读取

    # ---------- 环境 ----------
    @property
    def base_url(self) -> str:
        return self._load()["env"]["base_url"]  # 站点根 URL

    @property
    def api_prefix(self) -> str:
        return self._load()["env"]["api_prefix"]  # API 前缀 /api

    @property
    def login_url(self) -> str:
        return self._load()["env"]["login_url"]  # 登录页路径

    @property
    def member_url(self) -> str:
        return self._load()["env"]["member_url"]  # 会员中心路径

    @property
    def cart_url(self) -> str:
        return self._load()["env"]["cart_url"]  # 购物车路径

    @property
    def checkout_url(self) -> str:
        return self._load()["env"]["checkout_url"]  # 结算页路径

    @property
    def order_list_url(self) -> str:
        return self._load()["env"]["order_list_url"]  # 订单列表路径

    @property
    def headless(self) -> bool:
        return self._load()["env"]["headless"]  # 是否无头模式

    # ---------- 等待 ----------
    @property
    def implicit_wait(self) -> int:
        return self._load()["wait"]["implicit_wait_sec"]  # 隐性等待秒数

    @property
    def explicit_wait(self) -> int:
        return self._load()["wait"]["explicit_wait_sec"]  # 显性等待秒数

    @property
    def popup_wait(self) -> int:
        return self._load()["wait"]["popup_wait_sec"]  # 弹窗等待秒数

    # ---------- 账号 ----------
    @property
    def username(self) -> str:
        return self._load()["account"]["username"]  # 测试用户名

    @property
    def password(self) -> str:
        return self._load()["account"]["password"]  # 测试密码

    @property
    def login_type(self) -> str:
        return self._load()["account"]["login_type"]  # 登录类型 password

    @property
    def wrong_password(self) -> str:
        return self._load()["negative"]["wrong_password"]  # 错误密码

    # ---------- 鉴权 ----------
    @property
    def token_cookie(self) -> str:
        return self._load()["auth"]["token_cookie"]  # accessToken Cookie 名

    @property
    def token_header(self) -> str:
        return self._load()["auth"]["token_header"]  # Authorization 头名

    @property
    def token_prefix(self) -> str:
        return self._load()["auth"]["token_prefix"]  # Bearer 前缀

    @property
    def login_body(self) -> dict:
        return self._load()["auth"]["login_body"]  # 登录 API 请求体模板

    # ---------- Token 复用 ----------
    @property
    def token_cache_file(self) -> str:
        return self._load()["token_cache"]["file"]  # token 缓存文件相对路径

    @property
    def token_env_var(self) -> str:
        return self._load()["token_cache"]["env_var"]  # 环境变量名

    @property
    def allow_ui_login_fallback(self) -> bool:
        return self._load()["token_cache"]["allow_ui_login_fallback"]  # 是否允许 UI 登录兜底

    @property
    def login_wait_sec(self) -> int:
        return self._load()["token_cache"]["login_wait_sec"]  # 登录成功等待秒数

    # ---------- 商品 ----------
    @property
    def product_id(self) -> int:
        return self._load()["products"]["default"]["product_id"]  # 商品 ID

    @property
    def product_sn(self) -> str:
        return self._load()["products"]["default"]["product_sn"]  # 商品 SN

    @property
    def merge_qty_first(self) -> int:
        return self._load()["products"]["merge_qty_first"]  # 首次加购数量

    @property
    def merge_qty_second(self) -> int:
        return self._load()["products"]["merge_qty_second"]  # 再次加购数量

    @property
    def update_qty_legal(self) -> int:
        return self._load()["products"]["update_qty_legal"]  # 合法改数量

    @property
    def over_stock_qty(self) -> int:
        return self._load()["products"]["over_stock_qty"]  # 超库存数量

    # ---------- 结算/支付 ----------
    @property
    def flow_type(self) -> int:
        return self._load()["checkout"]["flow_type"]  # 结算 flow_type

    @property
    def pay_type_id(self) -> int:
        return self._load()["checkout"]["pay_type_id"]  # 支付方式 ID

    @property
    def shipping_type(self) -> list:
        return self._load()["checkout"]["shipping_type"]  # 配送方式

    @property
    def pay_type(self) -> str:
        return self._load()["payment"]["pay_type"]  # 在线支付类型

    @property
    def expected_pending_status(self) -> str:
        return self._load()["payment"]["expected_pending_status"]  # 待支付文案

    @property
    def expected_paid_status(self) -> str:
        return self._load()["payment"]["expected_paid_status"]  # 已支付文案

    def product_path(self, product_sn: str | None = None) -> str:
        """生成商品详情页路径 /item/{sn}。"""
        sn = product_sn or self.product_sn  # 自定义：默认用配置 SN
        pattern = self._load()["env"]["product_url_pattern"]  # 路径模板
        return pattern.replace("{product_sn}", sn)  # 自定义：替换占位符

    def api_url(self, path: str) -> str:
        """拼接完整 API URL。"""
        path = path if path.startswith("/") else f"/{path}"  # 自定义：保证前导斜杠
        if path.startswith(self.api_prefix):  # 已含前缀则直接拼 base
            return f"{self.base_url}{path}"
        return f"{self.base_url}{self.api_prefix}{path}"  # base + prefix + path


# 模块级单例，各层通过 from config.settings import config 引用
config = Config()  # 自定义：全局配置实例
