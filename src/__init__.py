"""
番茄小说下载器 - 模块化重构版本

这是重构后的模块化版本，提供更好的代码组织和维护性。

主要模块：
- core: 核心业务逻辑
- ui: 用户界面
- utils: 工具函数
- config: 配置管理
- services: 服务层
"""

__version__ = "2.0.0-refactor"
__author__ = "Tomato Novel Downloader Team"

# 导出主要接口
from .core import NovelDownloader
from .ui import NovelDownloaderGUI
from .config import get_config, save_config

__all__ = [
    "NovelDownloader",
    "NovelDownloaderGUI", 
    "get_config",
    "save_config"
]
