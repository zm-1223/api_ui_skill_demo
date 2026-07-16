"""Token 本地缓存与校验：复用 accessToken，避免每条用例重复 UI 登录。"""
import json  # 框架标准库：读写 JSON
import logging  # 框架标准库：日志
import os  # 框架标准库：环境变量
from datetime import datetime, timezone  # 框架标准库：记录更新时间
from pathlib import Path  # 框架标准库：路径

import requests  # 第三方 requests：校验 token 是否有效

from config.settings import config  # 自定义调用：全局配置

logger = logging.getLogger("tigshop_test.token")  # Token 模块 logger

# 进程内缓存：同一次 pytest 会话只校验/加载一次
_SESSION_TOKEN: str | None = None  # 自定义：模块级内存缓存


class TokenStore:
    """管理 accessToken 的读取、校验、持久化与进程内复用。"""

    @classmethod
    def get_token_path(cls) -> Path:
        """返回 token 缓存文件路径（默认 data/token.json）。"""
        rel = config.token_cache_file  # 自定义配置：相对路径
        return config.ROOT_DIR / rel  # 拼成绝对路径

    @classmethod
    def load_from_env(cls) -> str | None:
        """从环境变量 TIGSHOP_ACCESS_TOKEN 读取 token。"""
        env_name = config.token_env_var  # 环境变量名
        value = os.environ.get(env_name, "").strip()  # 框架 os：读环境变量
        return value or None  # 空串视为未设置

    @classmethod
    def load_from_file(cls) -> str | None:
        """从 data/token.json 读取 access_token 字段。"""
        path = cls.get_token_path()  # 缓存文件路径
        if not path.exists():  # 文件不存在
            return None  # 无缓存
        try:
            data = json.loads(path.read_text(encoding="utf-8"))  # 框架：解析 JSON
            token = (data.get("access_token") or data.get("token") or "").strip()  # 取 access_token 或 token
            return token or None  # 空则 None
        except Exception as exc:  # 解析失败
            logger.warning("读取 token 文件失败: %s", exc)  # 日志
            return None  # 视为无缓存

    @classmethod
    def save_to_file(cls, token: str) -> None:
        """将有效 token 写入 data/token.json，便于下次直接复用。"""
        path = cls.get_token_path()  # 目标路径
        path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        payload = {
            "access_token": token,  # 写入 token
            "updated_at": datetime.now(timezone.utc).isoformat(),  # UTC 时间戳
            "note": "由自动化测试写入；也可手动从浏览器 Cookie 复制 accessToken",
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )  # 框架 Path：写 JSON
        logger.info("已保存 token 到 %s", path)  # 日志

    @classmethod
    def is_valid(cls, token: str) -> bool:
        """调用 getCount 接口校验 token 是否仍有效。"""
        if not token:  # 空 token
            return False  # 无效
        try:
            url = config.api_url("/cart/cart/getCount")  # 自定义：轻量鉴权接口
            headers = {config.token_header: f"{config.token_prefix}{token}"}  # Bearer
            cookies = {config.token_cookie: token}  # Cookie 双通道
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)  # GET
            if resp.status_code != 200:  # HTTP 非 200
                return False  # 无效
            body = resp.json()  # 解析业务码
            return body.get("code") == 0  # code=0 表示鉴权成功
        except Exception as exc:  # 网络等异常
            logger.warning("校验 token 异常: %s", exc)  # 日志
            return False  # 保守视为无效

    @classmethod
    def resolve(cls, *, force_refresh: bool = False) -> str:
        """
        获取可用 token，优先级：
        1. 进程内缓存  2. 环境变量  3. token.json  4. UI 登录（若开启 fallback）
        """
        global _SESSION_TOKEN  # 自定义：引用模块级缓存
        if not force_refresh and _SESSION_TOKEN and cls.is_valid(_SESSION_TOKEN):  # 内存命中
            logger.info("复用进程内缓存 token")  # 日志
            return _SESSION_TOKEN  # 直接返回

        candidates: list[tuple[str, str | None]] = [
            ("env", cls.load_from_env()),  # 环境变量
            ("file", cls.load_from_file()),  # 本地文件
        ]
        for source, token in candidates:  # 依次尝试
            if token and cls.is_valid(token):  # 有效则采用
                logger.info("复用 %s 中的 token", source)  # 日志
                _SESSION_TOKEN = token  # 写入内存
                if source == "env":  # 来自环境变量也落盘方便下次
                    cls.save_to_file(token)  # 可选持久化
                return token  # 返回

        if config.allow_ui_login_fallback:  # 允许 UI 登录兜底
            from api.auth_helper import AuthHelper  # 延迟导入避免循环

            logger.warning("缓存 token 无效，回退 UI 登录（可能触发滑块）")  # 提示
            token = AuthHelper.login_via_ui(headless=config.headless)  # UI 登录
            cls.save_to_file(token)  # 保存供下次使用
            _SESSION_TOKEN = token  # 内存缓存
            return token  # 返回

        raise RuntimeError(
            "无可用 accessToken。请任选一种方式提供后重试：\n"
            f"  1. 环境变量 {config.token_env_var}=<token>\n"
            f"  2. 编辑 {cls.get_token_path()} 填入 access_token\n"
            "  3. 浏览器登录 demo.tigshop.cn → F12 → Cookie → 复制 accessToken\n"
            "  4. 在 data/test_data.json 设置 token_cache.allow_ui_login_fallback=true（可能遇滑块）"
        )  # 明确指引用户

    @classmethod
    def clear_session_cache(cls) -> None:
        """清空进程内 token 缓存（调试用）。"""
        global _SESSION_TOKEN  # 模块级变量
        _SESSION_TOKEN = None  # 置空
