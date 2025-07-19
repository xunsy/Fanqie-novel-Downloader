"""
文件操作工具模块

包含文件路径处理、文件名清理等文件相关的工具函数
"""

import os
import sys
import re
from typing import Optional


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，优先使用程序运行目录或可执行文件所在目录。
    确保配置文件等资源能够持久化保存，不会因为程序重启而丢失。

    Args:
        relative_path (str): 相对于程序目录的路径

    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # 优先使用可执行文件所在目录（适用于打包后的环境）
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            # PyInstaller打包环境：使用可执行文件所在目录
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境：使用脚本所在目录
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        # 备用方案：使用当前工作目录
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不合法字符。
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return "未命名文件"
    
    # Windows和Unix系统都不允许的字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 移除前后空格和点
    filename = filename.strip(' .')
    
    # 替换连续的下划线
    filename = re.sub(r'_{2,}', '_', filename)
    
    # 限制长度（考虑文件系统限制）
    max_length = 200
    if len(filename.encode('utf-8')) > max_length:
        # 按字节长度截断，确保不会截断UTF-8字符
        filename_bytes = filename.encode('utf-8')[:max_length]
        # 找到最后一个完整的UTF-8字符边界
        while filename_bytes:
            try:
                filename = filename_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                filename_bytes = filename_bytes[:-1]
    
    # 确保文件名不为空
    if not filename or filename == '_':
        filename = "未命名文件"
    
    return filename


def ensure_directory_exists(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[int]: 文件大小（字节），失败返回None
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return None


def check_disk_space(directory: str, required_space: int = 10 * 1024 * 1024) -> bool:
    """
    检查磁盘空间是否足够
    
    Args:
        directory: 目录路径
        required_space: 需要的空间（字节），默认10MB
        
    Returns:
        bool: 空间足够返回True
    """
    try:
        import shutil
        free_space = shutil.disk_usage(directory).free
        return free_space >= required_space
    except Exception:
        return True  # 检查失败时假设空间足够


__all__ = [
    "resource_path",
    "sanitize_filename", 
    "ensure_directory_exists",
    "get_file_size",
    "check_disk_space"
]
