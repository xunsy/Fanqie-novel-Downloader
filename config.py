"""
全局配置文件管理模块。

定义默认配置，并提供加载和保存用户自定义配置的功能。
用户配置存储在操作系统推荐的标准用户数据目录中，以实现跨平台兼容性。
"""

import os
import json
import sys
from typing import Dict, Any, List
import atexit
import time
import copy
import platformdirs

# --- 应用信息 ---
APP_NAME = "TomatoNovelDownloader"
APP_AUTHOR = "User"

# --- 配置文件路径管理 ---

def get_user_config_path() -> str:
    """
    获取跨平台的用户配置文件路径。
    使用 platformdirs 确保配置文件存储在操作系统推荐的位置。
    """
    config_dir = platformdirs.user_config_path(APP_NAME, APP_AUTHOR)
    # 确保目录存在
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "user_config.json")


# --- 默认配置常量 ---

# 默认主窗口几何尺寸和位置
DEFAULT_WINDOW_CONFIG: Dict[str, Any] = {
    "default_geometry": "1300x850",
    "position": None
}

# 默认网络请求相关配置
REQUEST_CONFIG: Dict[str, Any] = {
    "max_workers": 50,
    "max_retries": 3,
    "timeout": 10,
    "request_rate_limit": 0.05,
    "default_download_channel": "official",
    "download_channels": {
        "official": {
            "name": "官方渠道",
            "enabled": True
        }
    },
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
}



# 默认输出相关配置
OUTPUT_CONFIG: Dict[str, Any] = {
    "generate_epub_when_txt_selected": False,
}

# 默认阅读器界面配置
READER_CONFIG: Dict[str, Any] = {
    "default_font": "Microsoft YaHei",
    "default_size": 14,
    "default_fg": "#DCE4EE",
    "default_bg": "#242424",
    "default_width": 1000,
    "default_height": 800,
    "padding": 10,
    "dark_mode": True,
    "auto_save_interval_ms": 30000
}

# 默认文件和路径相关配置
FILE_CONFIG: Dict[str, str] = {
    "status_file_format": ".{book_id}.download_status",
    "default_save_path": "downloads",  # 保留向后兼容性
    "last_save_path": ""  # 用户上次选择的保存路径，空字符串表示首次使用
}

# UI 主题配置 - 强制深色模式
APPEARANCE_CONFIG: Dict[str, str] = {
    "appearance_mode": "dark",  # 强制深色模式，不受系统主题影响
    "color_theme": "blue"
}

# Tor网络配置
TOR_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "proxy_port": 9050,
    "max_retries": 3,
    "change_ip_after": 980,
    "request_timeout": 35
}

# Cloudflare Workers反代配置
CLOUDFLARE_PROXY_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "proxy_domain": "",
    "fallback_to_original": True,
    "test_endpoint": "/test"
}

# --- 合并的默认配置 --- #
DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "window": DEFAULT_WINDOW_CONFIG,
    "request": REQUEST_CONFIG,
    "output": OUTPUT_CONFIG,
    "reader": READER_CONFIG,
    "file": FILE_CONFIG,
    "appearance": APPEARANCE_CONFIG,
    "tor": TOR_CONFIG,
    "cloudflare_proxy": CLOUDFLARE_PROXY_CONFIG
}

# 用户配置文件路径
USER_CONFIG_FILE_PATH = get_user_config_path()

def load_user_config() -> Dict[str, Dict[str, Any]]:
    """加载用户配置文件"""
    print(f"尝试加载用户配置文件: {USER_CONFIG_FILE_PATH}")
    
    config = copy.deepcopy(DEFAULT_CONFIG)
    
    if os.path.exists(USER_CONFIG_FILE_PATH):
        try:
            with open(USER_CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            def update_recursive(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        update_recursive(target[key], value)
                    else:
                        target[key] = value
            
            if isinstance(user_config, dict):
                update_recursive(config, user_config)
                print("成功加载并合并用户配置。")
            else:
                print(f"警告: 用户配置文件格式错误，已忽略。")
                
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件JSON解析错误: {str(e)}。将使用默认配置。")
            config = copy.deepcopy(DEFAULT_CONFIG)
        except Exception as e:
            print(f"错误: 加载配置文件时发生错误: {str(e)}。将使用默认配置。")
            config = copy.deepcopy(DEFAULT_CONFIG)
    else:
        print(f"未找到用户配置文件，将使用默认配置。")
    
    # 配置验证
    try:
        if not isinstance(config.get("request", {}).get("max_workers"), int) or not (1 <= config["request"]["max_workers"] <= 50):
            config["request"]["max_workers"] = 50
    except Exception:
        if "request" not in config: config["request"] = {}
        config["request"]["max_workers"] = 5
    
    try:
        if not isinstance(config.get("request", {}).get("timeout"), (int, float)) or config["request"]["timeout"] <= 0:
            config["request"]["timeout"] = 10
    except Exception:
        if "request" not in config: config["request"] = {}
        config["request"]["timeout"] = 10
    
    return config

def save_user_config(config_to_save: Dict[str, Dict[str, Any]]) -> bool:
    """保存用户配置到文件"""
    temp_file_path = f"{USER_CONFIG_FILE_PATH}.temp"
    print(f"尝试保存用户配置到: {USER_CONFIG_FILE_PATH}")
    
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, ensure_ascii=False, indent=4)
        
        os.replace(temp_file_path, USER_CONFIG_FILE_PATH)
        print("用户配置保存成功。")
        return True
        
    except Exception as e:
        print(f"错误: 保存用户配置失败: {str(e)}")
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        return False

# 全局配置变量
CONFIG: Dict[str, Dict[str, Any]] = load_user_config()

# 在程序退出时自动保存配置
_save_on_exit_registered = False
def register_save_on_exit():
    global _save_on_exit_registered
    if not _save_on_exit_registered:
        atexit.register(lambda: save_user_config(CONFIG))
        print("已注册退出时自动保存配置。")
        _save_on_exit_registered = True

register_save_on_exit()

if __name__ == "__main__":
    print("--- 当前加载的配置 ---")
    print(json.dumps(CONFIG, indent=4, ensure_ascii=False))
