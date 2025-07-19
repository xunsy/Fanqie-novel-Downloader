"""
核心业务模块

包含小说下载的核心业务逻辑：
- models: 数据模型
- downloaders: 下载器实现
- storage: 存储管理
"""

from .downloaders import NovelDownloader
from .models import Novel, Chapter

__all__ = [
    "NovelDownloader",
    "Novel", 
    "Chapter"
]
