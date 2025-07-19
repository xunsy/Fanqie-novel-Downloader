"""
下载器模块

包含各种下载策略的实现：
- base: 下载器基类
- batch_downloader: 批量下载器
- single_downloader: 单章下载器
- api_manager: API管理器
"""

from .base import BaseDownloader
from .novel_downloader import NovelDownloader

__all__ = [
    "BaseDownloader",
    "NovelDownloader"
]
