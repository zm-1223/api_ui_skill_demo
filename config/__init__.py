# config 包初始化：导出全局配置对象 Config，供 tests/ui/api 模块引用
from config.settings import Config  # 自定义调用：从 settings 模块导入 Config 单例

__all__ = ["Config"]  # 定义包对外暴露的符号列表
