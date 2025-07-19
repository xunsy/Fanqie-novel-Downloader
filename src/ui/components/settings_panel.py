"""
设置面板组件

负责应用设置的UI界面
"""

import customtkinter as ctk
from typing import Callable, Optional

try:
    from ...config.settings import get_config, set_config
except ImportError:
    try:
        from config.settings import get_config, set_config
    except ImportError:
        # 创建占位符函数
        def get_config(key=None, default=None):
            return default if key else {}
        def set_config(key, value):
            pass


class SettingsPanel(ctk.CTkFrame):
    """设置面板组件"""
    
    def __init__(self, parent, config_changed_callback: Callable = None):
        """
        初始化设置面板
        
        Args:
            parent: 父组件
            config_changed_callback: 配置改变回调函数
        """
        super().__init__(parent)
        
        self.config_changed_callback = config_changed_callback
        self.config = get_config()
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_widgets()
        self._load_settings()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建滚动框架
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 下载设置
        self._create_download_settings()
        
        # 网络设置
        self._create_network_settings()
        
        # 界面设置
        self._create_ui_settings()
        
        # 按钮区域
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_button = ctk.CTkButton(
            button_frame, 
            text="保存设置", 
            command=self._save_settings,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_button.pack(side="left", padx=10, pady=10)
        
        self.reset_button = ctk.CTkButton(
            button_frame, 
            text="重置为默认", 
            command=self._reset_settings,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.reset_button.pack(side="left", padx=10, pady=10)
    
    def _create_download_settings(self):
        """创建下载设置"""
        download_frame = ctk.CTkFrame(self.scrollable_frame)
        download_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(download_frame, text="下载设置", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 最大并发数
        workers_frame = ctk.CTkFrame(download_frame)
        workers_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(workers_frame, text="最大并发数:").pack(side="left", padx=10, pady=10)
        self.max_workers_var = ctk.StringVar(value="4")
        self.max_workers_entry = ctk.CTkEntry(workers_frame, textvariable=self.max_workers_var, width=100)
        self.max_workers_entry.pack(side="left", padx=10, pady=10)
        
        # 请求超时
        timeout_frame = ctk.CTkFrame(download_frame)
        timeout_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(timeout_frame, text="请求超时(秒):").pack(side="left", padx=10, pady=10)
        self.timeout_var = ctk.StringVar(value="15")
        self.timeout_entry = ctk.CTkEntry(timeout_frame, textvariable=self.timeout_var, width=100)
        self.timeout_entry.pack(side="left", padx=10, pady=10)
        
        # 最大重试次数
        retries_frame = ctk.CTkFrame(download_frame)
        retries_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(retries_frame, text="最大重试次数:").pack(side="left", padx=10, pady=10)
        self.max_retries_var = ctk.StringVar(value="3")
        self.max_retries_entry = ctk.CTkEntry(retries_frame, textvariable=self.max_retries_var, width=100)
        self.max_retries_entry.pack(side="left", padx=10, pady=10)
        
        # 请求间隔
        rate_limit_frame = ctk.CTkFrame(download_frame)
        rate_limit_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(rate_limit_frame, text="请求间隔(秒):").pack(side="left", padx=10, pady=10)
        self.rate_limit_var = ctk.StringVar(value="0.5")
        self.rate_limit_entry = ctk.CTkEntry(rate_limit_frame, textvariable=self.rate_limit_var, width=100)
        self.rate_limit_entry.pack(side="left", padx=10, pady=10)
    
    def _create_network_settings(self):
        """创建网络设置"""
        network_frame = ctk.CTkFrame(self.scrollable_frame)
        network_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(network_frame, text="网络设置", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 代理设置
        self.enable_proxy_var = ctk.BooleanVar(value=False)
        self.enable_proxy_check = ctk.CTkCheckBox(network_frame, text="启用代理", variable=self.enable_proxy_var)
        self.enable_proxy_check.pack(anchor="w", padx=10, pady=5)
        
        # 代理地址
        proxy_frame = ctk.CTkFrame(network_frame)
        proxy_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(proxy_frame, text="代理地址:").pack(side="left", padx=10, pady=10)
        self.proxy_host_var = ctk.StringVar(value="")
        self.proxy_host_entry = ctk.CTkEntry(proxy_frame, textvariable=self.proxy_host_var, width=150)
        self.proxy_host_entry.pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(proxy_frame, text="端口:").pack(side="left", padx=10, pady=10)
        self.proxy_port_var = ctk.StringVar(value="")
        self.proxy_port_entry = ctk.CTkEntry(proxy_frame, textvariable=self.proxy_port_var, width=80)
        self.proxy_port_entry.pack(side="left", padx=10, pady=10)
    
    def _create_ui_settings(self):
        """创建界面设置"""
        ui_frame = ctk.CTkFrame(self.scrollable_frame)
        ui_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ui_frame, text="界面设置", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 外观模式
        appearance_frame = ctk.CTkFrame(ui_frame)
        appearance_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(appearance_frame, text="外观模式:").pack(side="left", padx=10, pady=10)
        self.appearance_var = ctk.StringVar(value="dark")
        self.appearance_menu = ctk.CTkOptionMenu(
            appearance_frame, 
            variable=self.appearance_var,
            values=["light", "dark", "system"],
            command=self._on_appearance_changed
        )
        self.appearance_menu.pack(side="left", padx=10, pady=10)
        
        # 颜色主题
        theme_frame = ctk.CTkFrame(ui_frame)
        theme_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(theme_frame, text="颜色主题:").pack(side="left", padx=10, pady=10)
        self.theme_var = ctk.StringVar(value="blue")
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["blue", "green", "dark-blue"],
            command=self._on_theme_changed
        )
        self.theme_menu.pack(side="left", padx=10, pady=10)
    
    def _load_settings(self):
        """加载设置"""
        # 下载设置
        self.max_workers_var.set(str(self.config.get('request.max_workers', 4)))
        self.timeout_var.set(str(self.config.get('request.timeout', 15)))
        self.max_retries_var.set(str(self.config.get('request.max_retries', 3)))
        self.rate_limit_var.set(str(self.config.get('request.request_rate_limit', 0.5)))
        
        # 网络设置
        self.enable_proxy_var.set(self.config.get('network.enable_proxy', False))
        self.proxy_host_var.set(self.config.get('network.proxy_host', ''))
        self.proxy_port_var.set(str(self.config.get('network.proxy_port', '')))
        
        # 界面设置
        self.appearance_var.set(self.config.get('ui.appearance_mode', 'dark'))
        self.theme_var.set(self.config.get('ui.color_theme', 'blue'))
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 下载设置
            set_config('request.max_workers', int(self.max_workers_var.get()))
            set_config('request.timeout', int(self.timeout_var.get()))
            set_config('request.max_retries', int(self.max_retries_var.get()))
            set_config('request.request_rate_limit', float(self.rate_limit_var.get()))
            
            # 网络设置
            set_config('network.enable_proxy', self.enable_proxy_var.get())
            set_config('network.proxy_host', self.proxy_host_var.get())
            if self.proxy_port_var.get():
                set_config('network.proxy_port', int(self.proxy_port_var.get()))
            
            # 界面设置
            set_config('ui.appearance_mode', self.appearance_var.get())
            set_config('ui.color_theme', self.theme_var.get())
            
            # 通知配置改变
            if self.config_changed_callback:
                self.config_changed_callback('all', 'saved')
            
            # 显示成功消息
            from tkinter import messagebox
            messagebox.showinfo("成功", "设置已保存")
            
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"设置值无效: {e}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _reset_settings(self):
        """重置设置"""
        from tkinter import messagebox
        if messagebox.askyesno("确认", "确定要重置所有设置为默认值吗？"):
            from ...config.settings import get_config_manager
            manager = get_config_manager()
            manager.reset_to_default()
            self._load_settings()
            messagebox.showinfo("成功", "设置已重置为默认值")
    
    def _on_appearance_changed(self, value):
        """外观模式改变"""
        ctk.set_appearance_mode(value)
    
    def _on_theme_changed(self, value):
        """主题改变"""
        ctk.set_default_color_theme(value)
    
    def refresh(self):
        """刷新面板"""
        self._load_settings()


__all__ = ["SettingsPanel"]
