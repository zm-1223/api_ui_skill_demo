"""日志工具：为 pytest 用例与 Page/API 操作提供统一文件日志。"""
import logging  # 框架标准库：日志模块
import os  # 框架标准库：目录操作
from datetime import datetime  # 框架标准库：时间戳
from pathlib import Path  # 框架标准库：路径

from config.settings import config  # 自定义调用：读取项目根目录


def setup_logger(name: str = "tigshop_test") -> logging.Logger:
    """创建并返回带文件与控制台输出的 logger。"""
    log_dir = config.ROOT_DIR / "logs"  # 自定义：日志目录 logs/
    log_dir.mkdir(parents=True, exist_ok=True)  # 框架：递归创建目录
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 框架：格式化时间
    log_file = log_dir / f"test_{ts}.log"  # 自定义：日志文件名

    logger = logging.getLogger(name)  # 框架 logging：获取命名 logger
    if logger.handlers:  # 自定义：避免重复添加 handler
        return logger

    logger.setLevel(logging.INFO)  # 框架：设置日志级别 INFO
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")  # 框架：格式

    fh = logging.FileHandler(log_file, encoding="utf-8")  # 框架：文件 handler
    fh.setFormatter(fmt)  # 框架：绑定格式
    logger.addHandler(fh)  # 框架：注册文件 handler

    ch = logging.StreamHandler()  # 框架：控制台 handler
    ch.setFormatter(fmt)  # 框架：绑定格式
    logger.addHandler(ch)  # 框架：注册控制台 handler

    return logger  # 返回配置好的 logger
