"""Allure 报告钩子：环境信息、失败截图附件、会话结束自动生成 HTML。"""
import logging  # 框架标准库：日志
import subprocess  # 框架标准库：调用 allure 命令行
import sys  # 框架标准库：sys.path
from pathlib import Path  # 框架标准库：路径

import pytest  # 框架 pytest：钩子与 fixture

# 项目根目录（tests 上一级）
ROOT = Path(__file__).resolve().parent.parent  # 自定义：定位根路径
if str(ROOT) not in sys.path:  # 避免重复插入
    sys.path.insert(0, str(ROOT))  # 加入 import 路径

from utils.logger_helper import setup_logger  # 自定义：日志初始化

logger = logging.getLogger("tigshop_test")  # 框架 logging：根 logger

# Allure 目录常量
ALLURE_RESULTS = ROOT / "reports" / "allure-results"  # pytest 写入的原始结果
ALLURE_REPORT_DIR = ROOT / "reports" / "allure-report"  # allure generate 输出目录


@pytest.fixture(scope="session")  # 框架 pytest：整个会话只解析一次 token
def shared_access_token():
    """
    会话级共享 accessToken（方案 B：Token 复用）。
    API/UI fixture 均注入此 token，避免每条用例重复 UI 登录触发滑块。
    """
    from api.auth_helper import AuthHelper  # 延迟导入：避免 pytest 收集阶段循环依赖

    token = AuthHelper.get_token()  # 自定义：env → file → 校验 → 可选 UI fallback
    logger.info("shared_access_token 已就绪，长度=%s", len(token))  # 日志（不打印明文）
    yield token  # 提供给 api_client / logged_in_driver 等 fixture
    logger.info("shared_access_token 会话结束")  # 会话收尾日志


def pytest_configure(config):  # 框架 pytest：启动配置钩子
    """创建 logs/reports/allure 目录并初始化 logger。"""
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)  # 日志目录
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)  # 报告根目录
    (ROOT / "reports" / "screenshots").mkdir(parents=True, exist_ok=True)  # UI 截图
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)  # Allure 原始结果
    ALLURE_REPORT_DIR.mkdir(parents=True, exist_ok=True)  # Allure HTML 目录
    setup_logger()  # 自定义：配置文件+控制台日志
    _write_allure_environment()  # 自定义：写入环境信息供 Allure 展示
    logger.info("pytest 会话开始，ROOT=%s", ROOT)  # 记录根路径


def _write_allure_environment() -> None:
    """写入 Allure environment.properties，展示站点与账号（不含密码）。"""
    try:
        from config.settings import config as cfg  # 自定义：读取配置
    except Exception:  # 配置加载失败则跳过
        return  # 不阻断测试
    env_file = ALLURE_RESULTS / "environment.properties"  # Allure 环境文件路径
    lines = [
        f"Base.URL={cfg.base_url}",  # 站点
        f"Username={cfg.username}",  # 账号
        f"Product.SN={cfg.product_sn}",  # 默认商品
        f"Implicit.Wait={cfg.implicit_wait}s",  # 隐性等待
        f"Explicit.Wait={cfg.explicit_wait}s",  # 显性等待
    ]
    env_file.write_text("\n".join(lines), encoding="utf-8")  # 框架 Path：写文件


def pytest_sessionfinish(session, exitstatus):  # 框架 pytest：会话结束钩子
    """测试结束后自动生成 Allure 可浏览器打开的 HTML 报告。"""
    if not ALLURE_RESULTS.exists():  # 无结果目录
        return  # 跳过
    if not any(ALLURE_RESULTS.iterdir()):  # 目录为空
        logger.warning("Allure 结果目录为空，跳过报告生成")  # 警告
        return  # 跳过
    _generate_allure_html()  # 自定义：生成 HTML


def _generate_allure_html() -> None:
    """调用 scripts/generate_allure_report 生成可浏览器打开的 Allure HTML。"""
    script = ROOT / "scripts" / "generate_allure_report.py"  # 生成脚本路径
    if not script.exists():  # 脚本缺失
        logger.warning("未找到 %s", script)  # 日志
        return  # 跳过
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )  # 框架：用当前 Python 执行脚本
        if result.stdout:  # 有标准输出
            print(result.stdout)  # 打印给用户（含 file:/// 路径）
        if result.returncode != 0 and result.stderr:  # 失败 stderr
            logger.warning("Allure 报告生成: %s", result.stderr)  # 日志
    except Exception as exc:  # 异常不阻断
        logger.error("调用 generate_allure_report 失败: %s", exc)  # 错误日志
