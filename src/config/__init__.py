"""
配置管理模块

负责应用配置的管理：
- settings: 配置设置
- constants: 常量定义
"""

from .settings import get_config, save_config, CONFIG
from .constants import *

__all__ = [
    "get_config",
    "save_config", 
    "CONFIG"
]
