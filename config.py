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
    "download_mode": "batch",  # 默认Dlmily模式(batch) 或 rabbits0209模式(single)
    "single_batch_size": 20,  # rabbits0209模式的批量请求大小（默认20章，平衡速度和稳定性）
    "max_batch_size": 290,     # Dlmity最大批量请求限制（290章）
    "min_batch_size": 1,       # 最小批量请求限制
    "batch_success_threshold": 0.8,  # 批量下载成功率阈值
    "rabbits0209_max_chapters": 30,  # rabbits0209模式最大章节限制
    "rabbits0209_enable_limit": True,  # 是否启用rabbits0209章节限制
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

# 章节矫正相关配置
CHAPTER_CORRECTION_CONFIG: Dict[str, Any] = {
    "enabled": True,  # 是否启用章节矫正功能
    "auto_correct": True,  # 是否自动矫正章节顺序
    "show_correction_report": True,  # 是否显示矫正报告
    "backup_original_order": True,  # 是否备份原始章节顺序
    "handle_special_chapters": True,  # 是否处理特殊章节（序章、番外等）
    "strict_number_extraction": False,  # 是否使用严格的章节号提取模式
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
    "cloudflare_proxy": CLOUDFLARE_PROXY_CONFIG,
    "chapter_correction": CHAPTER_CORRECTION_CONFIG
}

# 用户配置文件路径
USER_CONFIG_FILE_PATH = get_user_config_path()

def validate_rabbits0209_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证并修正rabbits0209相关配置
    
    Args:
        config: 包含rabbits0209配置的字典
        
    Returns:
        修正后的配置字典
    """
    try:
        # 验证最大章节数
        if "rabbits0209_max_chapters" in config:
            old_chapters = config["rabbits0209_max_chapters"]
            new_chapters = validate_rabbits0209_max_chapters(old_chapters)
            if old_chapters != new_chapters:
                config["rabbits0209_max_chapters"] = new_chapters
        
        # 验证启用状态
        if "rabbits0209_enable_limit" in config:
            enable_limit = config["rabbits0209_enable_limit"]
            if not isinstance(enable_limit, bool):
                print(f"警告: rabbits0209_enable_limit配置无效 '{enable_limit}'，使用默认值True")
                config["rabbits0209_enable_limit"] = True
        
        # 协调rabbits0209_max_chapters与single_batch_size的关系
        if ("rabbits0209_max_chapters" in config and 
            "single_batch_size" in config and 
            config.get("rabbits0209_enable_limit", True)):
            
            max_chapters = config["rabbits0209_max_chapters"]
            batch_size = config["single_batch_size"]
            
            # 如果启用了章节限制，确保批量大小不超过章节限制
            if batch_size > max_chapters:
                print(f"提示: single_batch_size ({batch_size}) 大于rabbits0209_max_chapters ({max_chapters})")
                print(f"在rabbits0209模式下，实际批量大小将限制为 {max_chapters} 章")
        
        return config
        
    except Exception as e:
        print(f"警告: 验证rabbits0209配置时发生错误 {str(e)}")
        return config

def validate_rabbits0209_max_chapters(chapters: Any) -> int:
    """
    验证并修正rabbits0209最大章节数配置
    
    Args:
        chapters: 待验证的最大章节数值
        
    Returns:
        修正后的有效章节数值
    """
    try:
        # 尝试转换为整数
        if isinstance(chapters, (int, float)):
            max_chapters = int(chapters)
        elif isinstance(chapters, str) and chapters.isdigit():
            max_chapters = int(chapters)
        else:
            print(f"警告: rabbits0209最大章节数配置无效 '{chapters}'，使用默认值30")
            return 30
        
        # 检查范围（1-30章）
        if max_chapters < 1:
            print(f"警告: rabbits0209最大章节数 {max_chapters} 小于最小值 1，已调整为 1")
            return 1
        elif max_chapters > 30:
            print(f"警告: rabbits0209最大章节数 {max_chapters} 超过最大值 30，已调整为 30")
            return 30
        else:
            return max_chapters
            
    except Exception as e:
        print(f"警告: 验证rabbits0209最大章节数时发生错误 {str(e)}，使用默认值30")
        return 30

def validate_batch_size(size: Any) -> int:
    """
    验证并修正批量大小配置
    
    Args:
        size: 待验证的批量大小值
        
    Returns:
        修正后的有效批量大小值
    """
    try:
        # 尝试转换为整数
        if isinstance(size, (int, float)):
            batch_size = int(size)
        elif isinstance(size, str) and size.isdigit():
            batch_size = int(size)
        else:
            print(f"警告: 批量大小配置无效 '{size}'，使用默认值100")
            return 100
        
        # 检查范围
        min_size = REQUEST_CONFIG["min_batch_size"]
        max_size = REQUEST_CONFIG["max_batch_size"]
        
        if batch_size < min_size:
            print(f"警告: 批量大小 {batch_size} 小于最小值 {min_size}，已调整为 {min_size}")
            return min_size
        elif batch_size > max_size:
            print(f"警告: 批量大小 {batch_size} 超过最大值 {max_size}，已调整为 {max_size}")
            return max_size
        else:
            return batch_size
            
    except Exception as e:
        print(f"警告: 验证批量大小时发生错误 {str(e)}，使用默认值100")
        return 100

def migrate_batch_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    迁移旧的批量配置到新格式
    
    Args:
        config: 用户配置字典
        
    Returns:
        迁移后的配置字典
    """
    try:
        if "request" in config and isinstance(config["request"], dict):
            request_config = config["request"]
            
            # 验证并修正single_batch_size
            if "single_batch_size" in request_config:
                old_size = request_config["single_batch_size"]
                new_size = validate_batch_size(old_size)
                if old_size != new_size:
                    print(f"配置迁移: 批量大小从 {old_size} 更新为 {new_size}")
                    request_config["single_batch_size"] = new_size
            
            # 添加缺失的新配置项
            if "max_batch_size" not in request_config:
                request_config["max_batch_size"] = REQUEST_CONFIG["max_batch_size"]
                print("配置迁移: 添加max_batch_size配置")
                
            if "min_batch_size" not in request_config:
                request_config["min_batch_size"] = REQUEST_CONFIG["min_batch_size"]
                print("配置迁移: 添加min_batch_size配置")
                
            if "batch_success_threshold" not in request_config:
                request_config["batch_success_threshold"] = REQUEST_CONFIG["batch_success_threshold"]
                print("配置迁移: 添加batch_success_threshold配置")
            
            # 验证并修正rabbits0209_max_chapters
            if "rabbits0209_max_chapters" in request_config:
                old_chapters = request_config["rabbits0209_max_chapters"]
                new_chapters = validate_rabbits0209_max_chapters(old_chapters)
                if old_chapters != new_chapters:
                    print(f"配置迁移: rabbits0209最大章节数从 {old_chapters} 更新为 {new_chapters}")
                    request_config["rabbits0209_max_chapters"] = new_chapters
            else:
                # 添加缺失的rabbits0209配置项
                request_config["rabbits0209_max_chapters"] = REQUEST_CONFIG["rabbits0209_max_chapters"]
                print("配置迁移: 添加rabbits0209_max_chapters配置")
            
            if "rabbits0209_enable_limit" not in request_config:
                request_config["rabbits0209_enable_limit"] = REQUEST_CONFIG["rabbits0209_enable_limit"]
                print("配置迁移: 添加rabbits0209_enable_limit配置")
            
            # 应用rabbits0209配置验证
            request_config = validate_rabbits0209_config(request_config)
        
        return config
        
    except Exception as e:
        print(f"警告: 配置迁移时发生错误 {str(e)}，保持原配置")
        return config

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
                # 先进行配置迁移
                user_config = migrate_batch_config(user_config)
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
    
    # 验证rabbits0209相关配置
    try:
        if "request" in config and isinstance(config["request"], dict):
            # 确保rabbits0209配置项存在
            if "rabbits0209_max_chapters" not in config["request"]:
                config["request"]["rabbits0209_max_chapters"] = REQUEST_CONFIG["rabbits0209_max_chapters"]
                print("配置验证: 添加缺失的rabbits0209_max_chapters配置")
            
            if "rabbits0209_enable_limit" not in config["request"]:
                config["request"]["rabbits0209_enable_limit"] = REQUEST_CONFIG["rabbits0209_enable_limit"]
                print("配置验证: 添加缺失的rabbits0209_enable_limit配置")
            
            # 应用rabbits0209配置验证
            config["request"] = validate_rabbits0209_config(config["request"])
    except Exception as e:
        print(f"警告: 验证rabbits0209配置时发生错误 {str(e)}，使用默认配置")
        if "request" not in config: config["request"] = {}
        config["request"]["rabbits0209_max_chapters"] = REQUEST_CONFIG["rabbits0209_max_chapters"]
        config["request"]["rabbits0209_enable_limit"] = REQUEST_CONFIG["rabbits0209_enable_limit"]
    
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
