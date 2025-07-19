"""
UI工具函数模块

包含窗口居中、UI辅助等界面相关的工具函数
"""

import tkinter as tk
from typing import Optional, Union


def center_window_over_parent(child_window, parent_window):
    """
    将子窗口居中显示在父窗口上方。
    
    Args:
        child_window: 子窗口对象
        parent_window: 父窗口对象
    """
    try:
        # 更新窗口以获取准确的尺寸
        child_window.update_idletasks()
        parent_window.update_idletasks()
        
        # 获取父窗口的位置和尺寸
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        # 获取子窗口的尺寸
        child_width = child_window.winfo_reqwidth()
        child_height = child_window.winfo_reqheight()
        
        # 计算居中位置
        x = parent_x + (parent_width - child_width) // 2
        y = parent_y + (parent_height - child_height) // 2
        
        # 确保窗口不会超出屏幕边界
        screen_width = child_window.winfo_screenwidth()
        screen_height = child_window.winfo_screenheight()
        
        x = max(0, min(x, screen_width - child_width))
        y = max(0, min(y, screen_height - child_height))
        
        child_window.geometry(f"+{x}+{y}")
        
    except Exception as e:
        print(f"居中窗口时出错: {e}")


def center_window_on_screen(window, width: Optional[int] = None, height: Optional[int] = None):
    """
    将窗口居中显示在屏幕上。
    
    Args:
        window: 要居中的窗口
        width: 窗口宽度（可选）
        height: 窗口高度（可选）
    """
    try:
        window.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 获取窗口尺寸
        if width is None:
            width = window.winfo_reqwidth()
        if height is None:
            height = window.winfo_reqheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    except Exception as e:
        print(f"居中窗口时出错: {e}")


def set_window_icon(window, icon_path: str) -> bool:
    """
    设置窗口图标
    
    Args:
        window: 窗口对象
        icon_path: 图标文件路径
        
    Returns:
        bool: 设置成功返回True
    """
    try:
        window.iconbitmap(icon_path)
        return True
    except Exception as e:
        print(f"设置窗口图标失败: {e}")
        return False


def configure_window_properties(window, title: str = None, resizable: tuple = None, 
                               topmost: bool = None, alpha: float = None):
    """
    配置窗口属性
    
    Args:
        window: 窗口对象
        title: 窗口标题
        resizable: 是否可调整大小 (width, height)
        topmost: 是否置顶
        alpha: 透明度 (0.0-1.0)
    """
    try:
        if title is not None:
            window.title(title)
        
        if resizable is not None:
            window.resizable(resizable[0], resizable[1])
        
        if topmost is not None:
            window.attributes('-topmost', topmost)
        
        if alpha is not None:
            window.attributes('-alpha', alpha)
            
    except Exception as e:
        print(f"配置窗口属性失败: {e}")


def get_screen_size() -> tuple:
    """
    获取屏幕尺寸
    
    Returns:
        tuple: (width, height)
    """
    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except Exception:
        return 1920, 1080  # 默认值


def scale_size_for_dpi(size: int, base_dpi: int = 96) -> int:
    """
    根据DPI缩放尺寸
    
    Args:
        size: 原始尺寸
        base_dpi: 基准DPI
        
    Returns:
        int: 缩放后的尺寸
    """
    try:
        root = tk.Tk()
        root.withdraw()
        current_dpi = root.winfo_fpixels('1i')
        root.destroy()
        
        scale_factor = current_dpi / base_dpi
        return int(size * scale_factor)
    except Exception:
        return size


def bind_escape_to_close(window):
    """
    绑定ESC键关闭窗口
    
    Args:
        window: 窗口对象
    """
    def on_escape(event):
        window.destroy()
    
    window.bind('<Escape>', on_escape)


__all__ = [
    "center_window_over_parent",
    "center_window_on_screen",
    "set_window_icon",
    "configure_window_properties", 
    "get_screen_size",
    "scale_size_for_dpi",
    "bind_escape_to_close"
]
