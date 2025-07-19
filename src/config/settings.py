"""
配置管理模块

提供统一的配置管理接口
"""

import os
import json
import copy
from typing import Dict, Any, Optional
from pathlib import Path

from .constants import DEFAULT_CONFIG


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 使用用户配置目录
            import platformdirs
            config_dir = platformdirs.user_config_path("TomatoNovelDownloader", "User")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
        
        self.config_file = config_file
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._merge_config(user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """合并用户配置"""
        def merge_dict(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self._config, user_config)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键如 'request.timeout'
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            Dict: 配置段内容
        """
        return self._config.get(section, {})
    
    def update_section(self, section: str, values: Dict[str, Any]):
        """
        更新配置段
        
        Args:
            section: 配置段名称
            values: 新的配置值
        """
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section].update(values)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self._config = copy.deepcopy(DEFAULT_CONFIG)
    
    def reset_section(self, section: str):
        """重置指定配置段为默认值"""
        if section in DEFAULT_CONFIG:
            self._config[section] = copy.deepcopy(DEFAULT_CONFIG[section])
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return copy.deepcopy(self._config)
    
    def validate_config(self) -> Dict[str, str]:
        """
        验证配置
        
        Returns:
            Dict: 验证错误信息，键为配置项，值为错误信息
        """
        errors = {}
        
        # 验证请求配置
        request_config = self.get_section('request')
        
        if request_config.get('max_workers', 0) <= 0:
            errors['request.max_workers'] = '最大并发数必须大于0'
        
        if request_config.get('timeout', 0) <= 0:
            errors['request.timeout'] = '请求超时时间必须大于0'
        
        if request_config.get('max_retries', 0) < 0:
            errors['request.max_retries'] = '最大重试次数不能小于0'
        
        # 验证下载配置
        download_config = self.get_section('download')
        
        if download_config.get('batch_size', 0) <= 0:
            errors['download.batch_size'] = '批量下载大小必须大于0'
        
        # 验证文件配置
        file_config = self.get_section('file')
        save_path = file_config.get('last_save_path', '')
        
        if save_path and not os.path.exists(os.path.dirname(save_path)):
            errors['file.last_save_path'] = '保存路径的父目录不存在'
        
        return errors
    
    def export_config(self, export_path: str):
        """
        导出配置到指定文件
        
        Args:
            export_path: 导出文件路径
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"导出配置失败: {e}")
    
    def import_config(self, import_path: str):
        """
        从指定文件导入配置
        
        Args:
            import_path: 导入文件路径
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            self._merge_config(imported_config)
        except Exception as e:
            print(f"导入配置失败: {e}")


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str = None, default: Any = None) -> Any:
    """
    获取配置值的便捷函数
    
    Args:
        key: 配置键，如果为None则返回所有配置
        default: 默认值
        
    Returns:
        Any: 配置值
    """
    manager = get_config_manager()
    if key is None:
        return manager.get_all()
    return manager.get(key, default)


def save_config():
    """保存配置的便捷函数"""
    manager = get_config_manager()
    manager.save_config()


def set_config(key: str, value: Any):
    """
    设置配置值的便捷函数
    
    Args:
        key: 配置键
        value: 配置值
    """
    manager = get_config_manager()
    manager.set(key, value)


# 为了向后兼容，保留原有的CONFIG变量
CONFIG = get_config()


__all__ = [
    "ConfigManager",
    "get_config_manager", 
    "get_config",
    "save_config",
    "set_config",
    "CONFIG"
]
