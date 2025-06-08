#!/usr/bin/env python3
"""
番茄小说下载器GUI界面
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import threading
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
import sys
from typing import List, Dict, Optional
import traceback

# 导入项目中的其他模块
try:
    from config import CONFIG, save_user_config
    from utils import center_window_over_parent, center_window_on_screen, generate_epub, EBOOKLIB_AVAILABLE
    from downloader import GUIdownloader
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# 设置 CustomTkinter 外观 - 强制深色模式
ctk.set_appearance_mode("dark")  # 强制深色模式，不受系统主题影响
ctk.set_default_color_theme(CONFIG.get("appearance", {}).get("color_theme", "blue"))

class NovelDownloaderGUI(ctk.CTk):
    """番茄小说下载器的主GUI窗口类"""
    
    def __init__(self):
        """初始化主窗口和应用程序状态"""
        super().__init__()

        # 强制设置深色主题，确保不受系统主题影响
        ctk.set_appearance_mode("dark")

        # 基本窗口设置
        self.version = "1.7"
        self.title(f"🍅 番茄小说下载器 Pro v{self.version} - 智能下载引擎")

        # 获取屏幕尺寸以实现响应式设计
        self._setup_responsive_sizing()

        # 设置主窗口背景色为深色
        self.configure(fg_color="#0a0e27")

        # 绑定窗口大小变化事件
        self.bind("<Configure>", self._on_window_resize)

        # 自定义颜色主题
        self.colors = {
            "primary": "#1f538d",      # 深蓝色
            "secondary": "#14375e",    # 更深蓝色
            "accent": "#00d4ff",       # 科技蓝
            "success": "#00ff88",      # 成功绿
            "warning": "#ffaa00",      # 警告橙
            "error": "#ff4757",        # 错误红
            "background": "#0a0e27",   # 深色背景
            "surface": "#1a1d3a",      # 表面色
            "text": "#ffffff",         # 主文本
            "text_secondary": "#b8bcc8" # 次要文本
        }

        # 状态变量
        self.is_downloading = False
        self.downloaded_chapters = set()
        self.download_thread: Optional[threading.Thread] = None
        self.current_fq_downloader: Optional[GUIdownloader] = None

        # 响应式设计变量 - 先初始化为默认值
        self.current_scale_factor = 1.0
        self.base_font_size = 12

        self._setup_ui()

        # 在UI设置完成后再应用响应式设置
        self.after(100, self._apply_initial_responsive_settings)

    def _setup_responsive_sizing(self):
        """设置响应式窗口大小"""
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 计算合适的窗口大小（屏幕的90%，但不超过最大值）
        max_width = min(1800, int(screen_width * 0.90))
        max_height = min(1200, int(screen_height * 0.90))

        # 设置最小尺寸（确保所有组件都能正常显示）- 增加最小宽度
        min_width = max(1200, int(screen_width * 0.5))
        min_height = max(700, int(screen_height * 0.4))

        # 默认窗口大小 - 显著增加默认宽度以提供更好的用户体验
        default_width = min(1500, max_width)  # 从1300增加到1500
        default_height = min(900, max_height)  # 从850增加到900

        # 应用设置
        self.geometry(f"{default_width}x{default_height}")
        self.minsize(min_width, min_height)
        self.maxsize(max_width, max_height)

        # 居中显示窗口
        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2
        self.geometry(f"{default_width}x{default_height}+{x}+{y}")

    def _on_window_resize(self, event):
        """窗口大小变化时的回调函数"""
        if event.widget == self:
            # 计算缩放因子
            current_width = self.winfo_width()
            current_height = self.winfo_height()

            # 基于宽度计算缩放因子（以1500px为基准）- 更新基准值
            width_scale = current_width / 1500
            height_scale = current_height / 900

            # 使用较小的缩放因子以确保内容不会溢出
            self.current_scale_factor = min(width_scale, height_scale, 1.3)  # 最大1.3倍
            self.current_scale_factor = max(self.current_scale_factor, 0.8)  # 最小0.8倍

            # 更新字体大小
            self._update_font_sizes()

    def _update_font_sizes(self):
        """根据缩放因子更新字体大小"""
        try:
            # 这里可以添加动态字体大小调整的逻辑
            # 由于CustomTkinter的限制，我们主要通过布局调整来实现响应式设计
            # 可以在这里触发界面重新布局
            self._update_responsive_layout()
        except Exception as e:
            print(f"更新字体大小时出错: {e}")

    def _update_responsive_layout(self):
        """更新响应式布局"""
        try:
            # 更新主窗口的边距
            current_width = self.winfo_width()
            current_height = self.winfo_height()

            # 根据窗口大小调整边距 - 减少边距以充分利用空间
            if current_width < 1200:
                # 小窗口时减少边距
                padx = 10
                pady = 10
            elif current_width > 1600:
                # 大窗口时适度增加边距
                padx = 20
                pady = 20
            else:
                # 正常大小 - 减少默认边距
                padx = 15
                pady = 15

            # 这里可以添加更多的响应式调整逻辑
            # 例如调整字体大小、组件间距等

        except Exception as e:
            print(f"更新响应式布局时出错: {e}")

    def _handle_small_screen_layout(self):
        """处理小屏幕的特殊布局"""
        try:
            current_width = self.winfo_width()
            current_height = self.winfo_height()

            # 如果窗口太小，可以考虑调整布局 - 更新断点以适应新的最小尺寸
            if current_width < 1200 or current_height < 750:
                # 小屏幕模式：减少边距，调整字体大小
                self.current_scale_factor = 0.85

                # 可以在这里添加更多小屏幕优化
                # 例如：隐藏某些非必要元素，调整布局方向等

            elif current_width > 1700:
                # 大屏幕模式：增加边距，适当放大字体
                self.current_scale_factor = 1.15

        except Exception as e:
            print(f"处理小屏幕布局时出错: {e}")

    def _ensure_components_visible(self):
        """确保所有组件都在可见区域内"""
        try:
            # 检查窗口内容是否超出可见区域
            self.update_idletasks()

            # 如果内容超出，可以考虑添加滚动条或调整布局
            # 这里主要是确保关键组件始终可见

        except Exception as e:
            print(f"确保组件可见时出错: {e}")

    def _apply_initial_responsive_settings(self):
        """在UI初始化完成后应用初始响应式设置"""
        try:
            # 确保窗口已经完全初始化
            self.update_idletasks()

            # 触发一次响应式布局更新
            self._handle_small_screen_layout()
            self._ensure_components_visible()

            print("✅ 响应式设置已应用")

        except Exception as e:
            print(f"应用初始响应式设置时出错: {e}")

    def _setup_ui(self):
        """设置主窗口的用户界面布局和组件 - 左右分布式设计"""
        # 配置主窗口的网格权重，实现左右分布布局
        self.grid_columnconfigure(0, weight=2)  # 左侧控制区域 - 增加权重以适应更多内容
        self.grid_columnconfigure(1, weight=3)  # 右侧日志区域 - 保持更大权重
        self.grid_rowconfigure(0, weight=1)     # 主要内容区域 - 可扩展
        self.grid_rowconfigure(1, weight=0)     # 底部状态栏 - 固定高度

        self._setup_left_panel()   # 左侧控制面板
        self._setup_right_panel()  # 右侧日志和进度面板
        self._setup_bottom_frame() # 底部状态栏

    def _setup_left_panel(self):
        """设置左侧控制面板"""
        # 创建左侧主控制面板（可滚动）
        left_panel = ctk.CTkScrollableFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["accent"],
            fg_color=self.colors["surface"]
        )
        left_panel.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")

        # 设置区域状态变量 - 始终展开
        self.settings_expanded = True

        self._setup_control_section(left_panel)
        self._setup_integrated_settings(left_panel)

    def _setup_control_section(self, parent):
        """设置控制区域（原主框架内容）"""
        # 在左侧面板内创建控制区域
        control_frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        control_frame.pack(fill="x", padx=15, pady=15)

        # 配置控制框架的网格权重
        control_frame.grid_columnconfigure(0, weight=0)  # 标签列 - 固定宽度
        control_frame.grid_columnconfigure(1, weight=1)  # 输入框列 - 可扩展
        control_frame.grid_columnconfigure(2, weight=0)  # 按钮列 - 固定宽度

        # 添加标题区域
        title_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 10), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            title_frame,
            text="🚀 智能下载控制台",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        title_label.pack(side="left")

        # 状态指示器
        self.connection_status = ctk.CTkLabel(
            title_frame,
            text="🟢 API已连接",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["success"]
        )
        self.connection_status.pack(side="right")

        # 第一行：小说ID输入
        id_label = ctk.CTkLabel(
            control_frame,
            text="📚 小说ID:",
            anchor="w",
            width=80,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"]
        )
        id_label.grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")

        self.novel_id = ctk.CTkEntry(
            control_frame,
            placeholder_text="🔍 输入小说ID或书名",
            height=35,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=11),
            fg_color=self.colors["background"],
            text_color=self.colors["text"]
        )
        self.novel_id.grid(row=1, column=1, padx=(0, 10), pady=10, sticky="ew")

        self.search_button = ctk.CTkButton(
            control_frame,
            text="🔍",
            command=self.handle_search_button_click,
            width=40,
            height=35,
            corner_radius=8,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"],
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.search_button.grid(row=1, column=2, padx=(0, 15), pady=10)

        # 第二行：保存路径
        path_label = ctk.CTkLabel(
            control_frame,
            text="💾 保存路径:",
            anchor="w",
            width=80,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"]
        )
        path_label.grid(row=2, column=0, padx=(15, 10), pady=10, sticky="w")

        self.save_path = ctk.CTkEntry(
            control_frame,
            placeholder_text="📁 选择保存位置",
            height=35,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=11),
            fg_color=self.colors["background"],
            text_color=self.colors["text"]
        )
        self.save_path.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="ew")

        browse_button = ctk.CTkButton(
            control_frame,
            text="📂",
            command=self.browse_folder,
            width=40,
            height=35,
            corner_radius=8,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"],
            font=ctk.CTkFont(size=11, weight="bold")
        )
        browse_button.grid(row=2, column=2, padx=(0, 15), pady=10)

        # 路径状态指示器
        self.path_status_label = ctk.CTkLabel(
            control_frame,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        self.path_status_label.grid(row=3, column=1, padx=(0, 10), pady=(0, 5), sticky="w")

        # 智能加载保存路径
        self._load_save_path()

        # 绑定路径输入框变化事件，实现自动保存
        self.save_path.bind('<KeyRelease>', self._on_save_path_changed)
        self.save_path.bind('<FocusOut>', self._on_save_path_changed)

        # 第三行：输出格式选择
        format_label = ctk.CTkLabel(
            control_frame,
            text="📄 输出格式:",
            anchor="w",
            width=80,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"]
        )
        format_label.grid(row=4, column=0, padx=(15, 10), pady=10, sticky="w")

        self.output_format = ctk.CTkSegmentedButton(
            control_frame,
            values=["📝 TXT", "📖 EPUB"],
            corner_radius=8,
            border_width=1,
            fg_color=self.colors["secondary"],
            selected_color=self.colors["accent"],
            selected_hover_color=self.colors["primary"],
            unselected_color=self.colors["surface"],
            unselected_hover_color=self.colors["secondary"],
            font=ctk.CTkFont(size=10, weight="bold"),
            height=30
        )
        self.output_format.grid(row=4, column=1, columnspan=2, padx=(0, 15), pady=10, sticky="w")
        self.output_format.set("📝 TXT")

        # 第四行：主要操作按钮
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, columnspan=3, padx=15, pady=15, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.download_button = ctk.CTkButton(
            button_frame,
            text="⚡ 开始下载",
            command=self.start_download,
            height=40,
            corner_radius=10,
            fg_color=self.colors["accent"],
            hover_color=self.colors["success"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.download_button.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")

        self.stop_download_button = ctk.CTkButton(
            button_frame,
            text="⏹️ 停止下载",
            command=self._handle_stop_download_click,
            height=40,
            corner_radius=10,
            fg_color=self.colors["error"],
            hover_color="#cc3a47",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.stop_download_button.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")

    def _setup_integrated_settings(self, parent):
        """设置集成的高级设置区域（分页式界面）"""
        # 创建设置容器框架
        self.settings_container = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        self.settings_container.pack(fill="x", padx=15, pady=(10, 15))

        # 创建设置标题栏和分页导航
        self.settings_header = ctk.CTkFrame(
            self.settings_container,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["accent"],
            fg_color=self.colors["surface"]
        )
        self.settings_header.pack(fill="x", padx=10, pady=10)
        self.settings_header.grid_columnconfigure(0, weight=1)
        self.settings_header.grid_columnconfigure(1, weight=0)

        # 设置标题
        settings_title = ctk.CTkLabel(
            self.settings_header,
            text="⚙️ 高级设置",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        settings_title.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        # 分页导航区域
        self._setup_page_navigation()

        # 创建分页内容容器
        self.settings_content_container = ctk.CTkFrame(
            self.settings_container,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["surface"],
            height=400
        )
        self.settings_content_container.pack(fill="x", padx=10, pady=(0, 10))

        # 初始化分页系统
        self.current_settings_page = 0
        self.settings_pages = []

        self._setup_settings_pages()

    def _setup_page_navigation(self):
        """设置分页导航区域"""
        # 分页导航框架
        nav_frame = ctk.CTkFrame(
            self.settings_header,
            fg_color="transparent"
        )
        nav_frame.grid(row=0, column=1, padx=15, pady=8, sticky="e")

        # 页面标签
        self.page_labels = ["⚡ 性能", "📄 输出", "🌐 网络"]

        # 创建分页按钮
        self.page_buttons = []
        for i, label in enumerate(self.page_labels):
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                command=lambda idx=i: self._switch_to_page(idx),
                width=80,
                height=28,
                corner_radius=6,
                fg_color=self.colors["secondary"] if i != 0 else self.colors["accent"],
                hover_color=self.colors["primary"],
                font=ctk.CTkFont(size=10, weight="bold")
            )
            btn.grid(row=0, column=i, padx=2)
            self.page_buttons.append(btn)

        # 页面指示器
        self.page_indicator = ctk.CTkLabel(
            nav_frame,
            text="1/3",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"],
            width=30
        )
        self.page_indicator.grid(row=0, column=len(self.page_labels), padx=(10, 0))

    def _switch_to_page(self, page_index):
        """切换到指定页面"""
        if 0 <= page_index < len(self.settings_pages):
            # 隐藏当前页面
            if hasattr(self, 'current_settings_page') and self.current_settings_page < len(self.settings_pages):
                self.settings_pages[self.current_settings_page].pack_forget()

            # 显示新页面
            self.settings_pages[page_index].pack(fill="both", expand=True, padx=10, pady=10)
            self.current_settings_page = page_index

            # 更新按钮状态
            for i, btn in enumerate(self.page_buttons):
                if i == page_index:
                    btn.configure(fg_color=self.colors["accent"])
                else:
                    btn.configure(fg_color=self.colors["secondary"])

            # 更新页面指示器
            self.page_indicator.configure(text=f"{page_index + 1}/{len(self.settings_pages)}")

    def _setup_settings_pages(self):
        """设置所有分页内容"""
        # 创建三个页面
        self._create_performance_page()  # 性能优化页面
        self._create_output_page()       # 输出设置页面
        self._create_network_page()      # 网络设置页面

        # 默认显示第一页
        if self.settings_pages:
            self._switch_to_page(0)

    def _create_performance_page(self):
        """创建性能优化设置页面"""
        # 创建性能页面框架
        perf_page = ctk.CTkScrollableFrame(
            self.settings_content_container,
            corner_radius=0,
            fg_color="transparent"
        )
        self.settings_pages.append(perf_page)

        # 页面标题
        page_title = ctk.CTkLabel(
            perf_page,
            text="⚡ 性能优化设置",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        page_title.pack(anchor="w", padx=15, pady=(15, 20))

        # 性能设置区域
        perf_frame = ctk.CTkFrame(
            perf_page,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        perf_frame.pack(fill="x", padx=15, pady=(0, 15))

        # 最大并发下载数
        workers_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        workers_frame.pack(fill="x", padx=15, pady=15)
        workers_frame.grid_columnconfigure(1, weight=1)

        workers_label = ctk.CTkLabel(
            workers_frame,
            text="🔄 并发下载数:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=100
        )
        workers_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

        self.workers_var = tk.IntVar(value=CONFIG["request"].get("max_workers", 3))
        workers_slider = ctk.CTkSlider(
            workers_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.workers_var,
            progress_color=self.colors["accent"],
            button_color=self.colors["success"],
            button_hover_color=self.colors["primary"],
            height=20
        )
        workers_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        workers_value_label = ctk.CTkLabel(
            workers_frame,
            textvariable=self.workers_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent"],
            width=30
        )
        workers_value_label.grid(row=0, column=2, padx=(10, 0), pady=5)
        workers_slider.configure(command=lambda v: workers_value_label.configure(text=str(int(v))))

        # 添加说明文字
        workers_desc = ctk.CTkLabel(
            workers_frame,
            text="💡 提示：并发数越高下载越快，但会增加服务器负载",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        workers_desc.grid(row=1, column=0, columnspan=3, padx=0, pady=(0, 5), sticky="w")

        # 请求超时时间
        timeout_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        timeout_frame.pack(fill="x", padx=15, pady=(0, 15))
        timeout_frame.grid_columnconfigure(1, weight=1)

        timeout_label = ctk.CTkLabel(
            timeout_frame,
            text="⏱️ 请求超时:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=100
        )
        timeout_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

        self.timeout_var = tk.IntVar(value=CONFIG.get("request", {}).get("timeout", 10))
        timeout_slider = ctk.CTkSlider(
            timeout_frame,
            from_=5,
            to=60,
            number_of_steps=11,
            variable=self.timeout_var,
            progress_color=self.colors["accent"],
            button_color=self.colors["success"],
            button_hover_color=self.colors["primary"],
            height=20
        )
        timeout_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        timeout_value_label = ctk.CTkLabel(
            timeout_frame,
            textvariable=self.timeout_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent"],
            width=30
        )
        timeout_value_label.grid(row=0, column=2, padx=(10, 0), pady=5)
        timeout_slider.configure(command=lambda v: timeout_value_label.configure(text=f"{int(v)}s"))

        # 添加说明文字
        timeout_desc = ctk.CTkLabel(
            timeout_frame,
            text="💡 提示：超时时间过短可能导致下载失败，过长会影响响应速度",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        timeout_desc.grid(row=1, column=0, columnspan=3, padx=0, pady=(0, 5), sticky="w")

        # 保存按钮（放在每个页面的底部）
        save_button = ctk.CTkButton(
            perf_page,
            text="💾 保存所有设置",
            command=self._save_integrated_settings,
            height=40,
            corner_radius=8,
            fg_color=self.colors["success"],
            hover_color="#00cc77",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        save_button.pack(fill="x", padx=15, pady=20)

    def _create_output_page(self):
        """创建输出设置页面"""
        # 创建输出页面框架
        output_page = ctk.CTkScrollableFrame(
            self.settings_content_container,
            corner_radius=0,
            fg_color="transparent"
        )
        self.settings_pages.append(output_page)

        # 页面标题
        page_title = ctk.CTkLabel(
            output_page,
            text="📄 输出格式设置",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        page_title.pack(anchor="w", padx=15, pady=(15, 20))

        # 输出设置区域
        output_frame = ctk.CTkFrame(
            output_page,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        output_frame.pack(fill="x", padx=15, pady=(0, 15))

        # EPUB自动生成选项
        epub_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        epub_frame.pack(fill="x", padx=15, pady=15)

        self.generate_epub_var = ctk.BooleanVar(value=CONFIG.get("output", {}).get("generate_epub_when_txt_selected", False))
        generate_epub_check = ctk.CTkCheckBox(
            epub_frame,
            text="📚 选择TXT格式时同时生成EPUB文件",
            variable=self.generate_epub_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        generate_epub_check.pack(anchor="w", pady=(0, 10))

        # 添加说明文字
        epub_desc = ctk.CTkLabel(
            epub_frame,
            text="💡 提示：启用此选项后，选择TXT格式下载时会额外生成EPUB格式文件",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        epub_desc.pack(anchor="w", pady=(0, 10))

        # 文件命名设置区域
        naming_frame = ctk.CTkFrame(
            output_page,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        naming_frame.pack(fill="x", padx=15, pady=(0, 15))

        naming_title = ctk.CTkLabel(
            naming_frame,
            text="📝 文件命名规则",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        naming_title.pack(anchor="w", padx=15, pady=(15, 10))

        # 文件名格式选项
        naming_options_frame = ctk.CTkFrame(naming_frame, fg_color="transparent")
        naming_options_frame.pack(fill="x", padx=15, pady=(0, 15))

        # 这里可以添加更多输出相关的设置选项
        naming_info = ctk.CTkLabel(
            naming_options_frame,
            text="📋 当前使用格式：[作者] - [书名].txt/epub",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text"]
        )
        naming_info.pack(anchor="w", pady=5)

        naming_desc = ctk.CTkLabel(
            naming_options_frame,
            text="💡 提示：文件名会自动处理特殊字符以确保兼容性",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        naming_desc.pack(anchor="w", pady=(0, 5))

        # 保存按钮（放在每个页面的底部）
        save_button = ctk.CTkButton(
            output_page,
            text="💾 保存所有设置",
            command=self._save_integrated_settings,
            height=40,
            corner_radius=8,
            fg_color=self.colors["success"],
            hover_color="#00cc77",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        save_button.pack(fill="x", padx=15, pady=20)

    def _create_network_page(self):
        """创建网络设置页面"""
        # 创建网络页面框架
        network_page = ctk.CTkScrollableFrame(
            self.settings_content_container,
            corner_radius=0,
            fg_color="transparent"
        )
        self.settings_pages.append(network_page)

        # 页面标题
        page_title = ctk.CTkLabel(
            network_page,
            text="🌐 网络代理设置",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        page_title.pack(anchor="w", padx=15, pady=(15, 20))

        # Tor网络设置区域
        tor_frame = ctk.CTkFrame(
            network_page,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        tor_frame.pack(fill="x", padx=15, pady=(0, 15))

        tor_title = ctk.CTkLabel(
            tor_frame,
            text="🔒 Tor代理设置",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        tor_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Tor启用开关
        tor_enable_frame = ctk.CTkFrame(tor_frame, fg_color="transparent")
        tor_enable_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.tor_enabled_var = ctk.BooleanVar(value=CONFIG.get("tor", {}).get("enabled", False))
        tor_enabled_check = ctk.CTkCheckBox(
            tor_enable_frame,
            text="🛡️ 启用Tor代理网络",
            variable=self.tor_enabled_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        tor_enabled_check.pack(anchor="w", pady=(0, 5))

        tor_desc = ctk.CTkLabel(
            tor_enable_frame,
            text="💡 提示：Tor代理可以提供匿名访问，但可能会降低下载速度",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        tor_desc.pack(anchor="w", pady=(0, 10))

        # Tor端口设置
        tor_port_frame = ctk.CTkFrame(tor_frame, fg_color="transparent")
        tor_port_frame.pack(fill="x", padx=15, pady=(0, 15))
        tor_port_frame.grid_columnconfigure(1, weight=1)

        tor_port_label = ctk.CTkLabel(
            tor_port_frame,
            text="🔌 代理端口:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=100
        )
        tor_port_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

        self.tor_port_var = ctk.IntVar(value=CONFIG.get("tor", {}).get("proxy_port", 9050))
        tor_port_entry = ctk.CTkEntry(
            tor_port_frame,
            textvariable=self.tor_port_var,
            width=100,
            height=30,
            corner_radius=6,
            border_width=1,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=11),
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        tor_port_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Cloudflare Workers反代设置区域
        proxy_frame = ctk.CTkFrame(
            network_page,
            corner_radius=8,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        proxy_frame.pack(fill="x", padx=15, pady=(0, 15))

        proxy_title = ctk.CTkLabel(
            proxy_frame,
            text="🌐 Cloudflare反代设置",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        proxy_title.pack(anchor="w", padx=15, pady=(15, 10))

        # 反代启用开关
        proxy_enable_frame = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        proxy_enable_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.proxy_enabled_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("enabled", False))
        proxy_enabled_check = ctk.CTkCheckBox(
            proxy_enable_frame,
            text="🚀 启用Cloudflare反代加速",
            variable=self.proxy_enabled_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        proxy_enabled_check.pack(anchor="w", pady=(0, 5))

        proxy_desc = ctk.CTkLabel(
            proxy_enable_frame,
            text="💡 提示：CF反代可以提高访问速度，特别适用于网络受限环境",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        proxy_desc.pack(anchor="w", pady=(0, 10))

        # 反代域名设置
        proxy_domain_frame = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        proxy_domain_frame.pack(fill="x", padx=15, pady=(0, 10))

        proxy_domain_label = ctk.CTkLabel(
            proxy_domain_frame,
            text="🔗 反代域名:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"]
        )
        proxy_domain_label.pack(anchor="w", pady=(0, 5))

        self.proxy_domain_var = ctk.StringVar(value=CONFIG.get("cloudflare_proxy", {}).get("proxy_domain", ""))
        proxy_domain_entry = ctk.CTkEntry(
            proxy_domain_frame,
            textvariable=self.proxy_domain_var,
            height=30,
            corner_radius=6,
            border_width=1,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=11),
            placeholder_text="your-worker.workers.dev",
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        proxy_domain_entry.pack(fill="x", pady=(0, 5))

        # 回退选项
        fallback_frame = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        fallback_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.fallback_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("fallback_to_original", True))
        fallback_check = ctk.CTkCheckBox(
            fallback_frame,
            text="🔄 连接失败时自动回退到原始地址",
            variable=self.fallback_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        fallback_check.pack(anchor="w", pady=(0, 5))

        fallback_desc = ctk.CTkLabel(
            fallback_frame,
            text="💡 提示：建议启用此选项以确保在反代失效时仍能正常下载",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        )
        fallback_desc.pack(anchor="w")

        # 保存按钮（放在每个页面的底部）
        save_button = ctk.CTkButton(
            network_page,
            text="💾 保存所有设置",
            command=self._save_integrated_settings,
            height=40,
            corner_radius=8,
            fg_color=self.colors["success"],
            hover_color="#00cc77",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        save_button.pack(fill="x", padx=15, pady=20)

    def _save_integrated_settings(self):
        """保存集成设置的配置"""
        try:
            # 保存性能设置
            CONFIG["request"]["max_workers"] = self.workers_var.get()
            CONFIG["request"]["timeout"] = self.timeout_var.get()

            # 保存输出设置
            if "output" not in CONFIG:
                CONFIG["output"] = {}
            CONFIG["output"]["generate_epub_when_txt_selected"] = self.generate_epub_var.get()

            # 保存Tor设置
            if "tor" not in CONFIG:
                CONFIG["tor"] = {}
            CONFIG["tor"]["enabled"] = self.tor_enabled_var.get()
            CONFIG["tor"]["proxy_port"] = self.tor_port_var.get()

            # 保存Cloudflare代理设置
            if "cloudflare_proxy" not in CONFIG:
                CONFIG["cloudflare_proxy"] = {}
            CONFIG["cloudflare_proxy"]["enabled"] = self.proxy_enabled_var.get()
            CONFIG["cloudflare_proxy"]["proxy_domain"] = self.proxy_domain_var.get()
            CONFIG["cloudflare_proxy"]["fallback_to_original"] = self.fallback_var.get()

            # 保存配置到文件
            from config import save_user_config
            save_user_config(CONFIG)

            # 更新Tor状态显示
            self.update_tor_status()

            self.log("✅ 设置已保存", "success")

        except Exception as e:
            self.log(f"❌ 保存设置时出错: {e}", "error")

    def _toggle_settings(self, event=None):
        """设置区域切换方法（已禁用，设置始终展开）"""
        # 此方法已被禁用，高级设置面板始终保持展开状态
        pass

    def get_output_format(self):
        """获取选择的输出格式（去除图标）"""
        format_text = self.output_format.get()
        if "TXT" in format_text:
            return "TXT"
        elif "EPUB" in format_text:
            return "EPUB"
        return "TXT"  # 默认值

    def _setup_right_panel(self):
        """设置右侧面板（进度和日志）"""
        # 创建右侧面板
        right_panel = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["accent"],
            fg_color=self.colors["surface"]
        )
        right_panel.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")

        # 配置右侧面板的内部布局
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=0)  # 进度区域 - 固定高度
        right_panel.grid_rowconfigure(1, weight=1)  # 日志区域 - 可扩展

        self._setup_progress_section(right_panel)
        self._setup_log_section(right_panel)

    def _setup_progress_section(self, parent):
        """设置显示下载进度条和状态标签的区域"""
        progress_frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        progress_frame.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        # 进度标题
        progress_title = ctk.CTkLabel(
            progress_frame,
            text="📊 下载进度监控",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        progress_title.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="w")

        # 进度条
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["secondary"],
            progress_color=self.colors["accent"]
        )
        self.progress_bar.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # 状态标签
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="🚀 系统就绪 - 等待下载指令",
            anchor="center",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"]
        )
        self.status_label.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")

        # 状态指示器框架
        status_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        status_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Tor状态标签
        tor_enabled = CONFIG.get("tor", {}).get("enabled", False)
        tor_status_text = "🔒 Tor: 已启用" if tor_enabled else "🔓 Tor: 已禁用"
        self.tor_status_label = ctk.CTkLabel(
            status_frame,
            text=tor_status_text,
            anchor="center",
            text_color=self.colors["success"] if tor_enabled else self.colors["warning"],
            font=ctk.CTkFont(size=10, weight="bold")
        )
        self.tor_status_label.grid(row=0, column=0, padx=5, pady=3)

        # API状态标签
        self.api_status_label = ctk.CTkLabel(
            status_frame,
            text="🌐 API: 已连接",
            anchor="center",
            text_color=self.colors["success"],
            font=ctk.CTkFont(size=10, weight="bold")
        )
        self.api_status_label.grid(row=0, column=1, padx=5, pady=3)

        # 速度显示标签
        self.speed_label = ctk.CTkLabel(
            status_frame,
            text="⚡ 速度: 待机中",
            anchor="center",
            text_color=self.colors["text_secondary"],
            font=ctk.CTkFont(size=10, weight="bold")
        )
        self.speed_label.grid(row=0, column=2, padx=5, pady=3)

    def _setup_log_section(self, parent):
        """设置包含日志输出文本框的区域"""
        log_frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["secondary"],
            fg_color=self.colors["background"]
        )
        log_frame.grid(row=1, column=0, padx=15, pady=(8, 15), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        # 日志标题框架
        log_title_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_title_frame.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="ew")
        log_title_frame.grid_columnconfigure(0, weight=1)
        log_title_frame.grid_columnconfigure(1, weight=0)
        log_title_frame.grid_columnconfigure(2, weight=0)

        # 日志标题
        log_title = ctk.CTkLabel(
            log_title_frame,
            text="🔍 实时日志监控",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        log_title.grid(row=0, column=0, sticky="w")

        # 清空日志按钮（集成到日志标题栏）
        clear_log_button = ctk.CTkButton(
            log_title_frame,
            text="🗑️ 清空",
            command=self.clear_log,
            width=80,
            height=28,
            corner_radius=8,
            fg_color=self.colors["warning"],
            hover_color="#e6940a",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        clear_log_button.grid(row=0, column=1, padx=(10, 10), sticky="e")

        # 日志状态指示器
        self.log_status = ctk.CTkLabel(
            log_title_frame,
            text="🟢 系统运行正常",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["success"]
        )
        self.log_status.grid(row=0, column=2, sticky="e")

        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            border_width=1,
            border_color=self.colors["surface"],
            fg_color=self.colors["surface"],
            text_color=self.colors["text"]
        )
        self.log_text.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.log_text.configure(state="disabled")

    def _setup_bottom_frame(self):
        """设置底部状态栏（仅包含版本信息）"""
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)  # 居中对齐

        # 版本信息标签（居中）
        version_label = ctk.CTkLabel(
            bottom_frame,
            text=f"🍅 番茄小说下载器 Pro v{self.version} | 智能下载引擎",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        version_label.grid(row=0, column=0, pady=8)

    def log(self, message: str, level: str = "info"):
        """向日志文本框添加一条带有时间戳和级别的消息"""
        import datetime

        # 获取当前时间
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据级别添加图标和颜色
        level_icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "download": "⬇️",
            "system": "🔧"
        }

        icon = level_icons.get(level, "ℹ️")
        formatted_message = f"[{timestamp}] {icon} {message}"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted_message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

        # 更新日志状态指示器
        if level == "error":
            self.log_status.configure(text="🔴 检测到错误", text_color=self.colors["error"])
        elif level == "warning":
            self.log_status.configure(text="🟡 注意警告", text_color=self.colors["warning"])
        elif level == "download":
            self.log_status.configure(text="🔵 正在下载", text_color=self.colors["accent"])
        else:
            self.log_status.configure(text="🟢 系统运行正常", text_color=self.colors["success"])

    def update_progress(self, value: float, status_text: str):
        """更新进度条和状态标签"""
        self.progress_var.set(value)
        self.progress_bar.set(value / 100)

        # 添加进度图标和颜色
        if value == 0:
            icon = "🚀"
            color = self.colors["text"]
        elif value < 25:
            icon = "🔄"
            color = self.colors["accent"]
        elif value < 50:
            icon = "⚡"
            color = self.colors["accent"]
        elif value < 75:
            icon = "🔥"
            color = self.colors["warning"]
        elif value < 100:
            icon = "🎯"
            color = self.colors["success"]
        else:
            icon = "🎉"
            color = self.colors["success"]

        formatted_status = f"{icon} {status_text} ({value:.1f}%)"
        self.status_label.configure(text=formatted_status, text_color=color)

        # 更新速度显示（模拟）
        if value > 0 and value < 100:
            self.speed_label.configure(text="⚡ 速度: 高速下载中", text_color=self.colors["success"])
        elif value == 100:
            self.speed_label.configure(text="✅ 速度: 下载完成", text_color=self.colors["success"])
        else:
            self.speed_label.configure(text="⚡ 速度: 待机中", text_color=self.colors["text_secondary"])

        self.update_idletasks()

    def update_tor_status(self):
        """更新Tor状态标签"""
        tor_enabled = CONFIG.get("tor", {}).get("enabled", False)
        tor_status_text = "🔒 Tor: 已启用" if tor_enabled else "🔓 Tor: 已禁用"
        text_color = "green" if tor_enabled else "orange"
        self.tor_status_label.configure(text=tor_status_text, text_color=text_color)

    def _load_save_path(self):
        """智能加载保存路径"""
        try:
            file_settings = CONFIG.get("file", {})
            if not isinstance(file_settings, dict):
                file_settings = {}

            # 获取上次保存的路径
            saved_path = file_settings.get("last_save_path", "")

            # 如果有保存的路径且路径有效，则加载它
            if saved_path and os.path.isdir(saved_path):
                self.save_path.insert(0, saved_path)
                self._update_path_status("✅ 路径有效", self.colors["success"])
                # 只有在log_text存在时才记录日志
                if hasattr(self, 'log_text'):
                    self.log(f"✅ 已加载上次使用的保存路径: {saved_path}", "info")
            else:
                # 首次启动或路径无效时，保持输入框为空
                self.save_path.configure(placeholder_text="📁 请选择保存位置（首次使用请点击文件夹图标选择）")
                if saved_path:  # 如果有保存的路径但无效
                    self._update_path_status("⚠️ 上次路径无效", self.colors["warning"])
                    # 只有在log_text存在时才记录日志
                    if hasattr(self, 'log_text'):
                        self.log(f"⚠️ 上次保存的路径无效: {saved_path}，请重新选择", "warning")
                else:
                    self._update_path_status("💡 请选择保存路径", self.colors["text_secondary"])
                    # 只有在log_text存在时才记录日志
                    if hasattr(self, 'log_text'):
                        self.log("💡 首次使用，请选择保存路径", "info")

        except Exception as e:
            print(f"加载保存路径时出错: {e}")
            self.save_path.configure(placeholder_text="📁 请选择保存位置")
            self._update_path_status("❌ 加载失败", self.colors["error"])
            # 只有在log_text存在时才记录日志
            if hasattr(self, 'log_text'):
                self.log(f"❌ 加载保存路径时出错: {e}", "error")

    def _update_path_status(self, message, color):
        """更新路径状态指示器"""
        try:
            self.path_status_label.configure(text=message, text_color=color)
        except Exception:
            pass  # 如果标签还未创建，忽略错误

    def _on_save_path_changed(self, event=None):
        """保存路径输入框内容变化时的处理"""
        # 延迟执行，避免频繁保存
        if hasattr(self, '_save_path_timer'):
            self.after_cancel(self._save_path_timer)

        self._save_path_timer = self.after(1000, self._save_path_to_config)  # 1秒后保存

    def _save_path_to_config(self):
        """保存路径到配置文件"""
        try:
            current_path = self.save_path.get().strip()
            if current_path:
                # 验证路径有效性
                if self._validate_save_path(current_path):
                    # 保存到配置
                    if 'file' not in CONFIG:
                        CONFIG['file'] = {}
                    CONFIG['file']['last_save_path'] = current_path
                    save_user_config(CONFIG)
                    self._update_path_status("✅ 路径已保存", self.colors["success"])
                    # 只有在log_text存在时才记录日志
                    if hasattr(self, 'log_text'):
                        self.log(f"💾 保存路径已更新: {current_path}", "success")
                else:
                    self._update_path_status("⚠️ 路径无效", self.colors["warning"])
                    # 只有在log_text存在时才记录日志
                    if hasattr(self, 'log_text'):
                        self.log(f"⚠️ 路径无效或无写入权限: {current_path}", "warning")
            else:
                self._update_path_status("💡 请选择保存路径", self.colors["text_secondary"])
        except Exception as e:
            self._update_path_status("❌ 保存失败", self.colors["error"])
            # 只有在log_text存在时才记录日志
            if hasattr(self, 'log_text'):
                self.log(f"❌ 保存路径配置时出错: {e}", "error")

    def _validate_save_path(self, path):
        """验证保存路径的有效性"""
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                # 尝试创建目录
                try:
                    os.makedirs(path, exist_ok=True)
                    return True
                except OSError:
                    return False

            # 检查是否为目录
            if not os.path.isdir(path):
                return False

            # 检查写入权限
            test_file = os.path.join(path, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except (OSError, IOError):
                return False

        except Exception:
            return False

    def browse_folder(self):
        """打开目录选择对话框以选择保存路径"""
        initial_dir = self.save_path.get().strip()
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()

        folder_path = filedialog.askdirectory(
            title="选择保存文件夹",
            initialdir=initial_dir
        )
        if folder_path:
            self.save_path.delete(0, "end")
            self.save_path.insert(0, folder_path)

            # 验证并保存路径
            if self._validate_save_path(folder_path):
                # 立即保存到配置文件
                if 'file' not in CONFIG:
                    CONFIG['file'] = {}
                CONFIG['file']['last_save_path'] = folder_path
                save_user_config(CONFIG)
                self._update_path_status("✅ 路径已设置", self.colors["success"])
                # 只有在log_text存在时才记录日志
                if hasattr(self, 'log_text'):
                    self.log(f"✅ 保存路径已设置: {folder_path}", "success")
            else:
                self._update_path_status("⚠️ 路径无写入权限", self.colors["warning"])
                # 只有在log_text存在时才记录日志
                if hasattr(self, 'log_text'):
                    self.log(f"⚠️ 选择的路径可能无写入权限: {folder_path}", "warning")

    def clear_log(self):
        """清空日志文本框"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def handle_search_button_click(self):
        """处理搜索按钮点击事件"""
        input_text = self.novel_id.get().strip()
        if not input_text:
            messagebox.showerror("错误", "请输入书名或小说ID")
            return

        # 这里可以添加搜索功能的实现
        self.log(f"搜索功能暂未实现，输入内容: {input_text}", "warning")
        messagebox.showinfo("提示", "搜索功能正在开发中，请直接输入小说ID进行下载")



    def _update_gui_progress_adapter(self, percent_int: int):
        """GUI进度更新适配器"""
        percent_int = max(0, min(100, percent_int))
        status_text = f"下载进度: {percent_int}%"
        if percent_int == 100:
            pass
        self.update_progress(float(percent_int), status_text)

    def _on_fq_download_complete(self):
        """下载完成回调"""
        self.log("下载线程结束。")
        self.download_button.configure(state="normal")
        self.stop_download_button.configure(state="disabled")
        self.is_downloading = False
        self.current_fq_downloader = None

    def _handle_stop_download_click(self):
        """处理停止下载按钮点击"""
        if self.current_fq_downloader and self.download_thread and self.download_thread.is_alive():
            self.log("正在发送停止下载信号...")
            self.current_fq_downloader.stop_download()
            self.stop_download_button.configure(state="disabled")
        else:
            self.log("没有活动的下载任务可以停止。")
            self.download_button.configure(state="normal")
            self.stop_download_button.configure(state="disabled")
            self.is_downloading = False

    def start_download(self):
        """开始下载"""
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showwarning("提示", "下载正在进行中！")
            return

        input_text = self.novel_id.get().strip()
        if not input_text:
            messagebox.showerror("错误", "请输入书名或小说ID")
            return

        # 检查输入是否为ID
        novel_ids = []
        parts = [part.strip() for part in input_text.split(',') if part.strip()]
        if parts and all(part.isdigit() for part in parts):
            novel_ids = parts
            self.log(f"检测到输入为 ID: {', '.join(novel_ids)}")
        else:
            self.log(f"检测到输入为书名: {input_text}，请点击 '搜索' 按钮查找书籍ID。")
            messagebox.showinfo("提示", f"检测到输入为书名'{input_text}'，请点击 '搜索' 按钮查找对应的书籍ID。")
            return

        book_id_to_download = novel_ids[0]
        if len(novel_ids) > 1:
            self.log(f"检测到多个ID，将只下载第一个: {book_id_to_download}")
            messagebox.showinfo("提示", f"检测到多个ID，当前版本将只下载第一个ID: {book_id_to_download}", parent=self)

        save_path = self.save_path.get().strip()
        if not save_path:
            # 如果没有选择保存路径，提示用户选择
            messagebox.showwarning("提示", "请先选择保存路径！\n\n点击路径输入框旁边的文件夹图标选择保存位置。")
            return

        self.download_button.configure(state="disabled")
        self.stop_download_button.configure(state="normal")
        self.is_downloading = True
        self.downloaded_chapters.clear()
        # 不要立即重置进度条，让下载器根据已下载章节设置初始进度
        self.status_label.configure(text="准备下载...")

        self.log(f"准备下载 ID: {book_id_to_download}")

        self.current_fq_downloader = GUIdownloader(
            book_id=book_id_to_download,
            save_path=save_path,
            status_callback=self.log,
            progress_callback=self._update_gui_progress_adapter
        )

        def download_thread_target_wrapper():
            try:
                if self.current_fq_downloader:
                    self.current_fq_downloader.run()
            except Exception as e_thread:
                self.log(f"下载线程中发生未捕获的错误: {e_thread}")
                import traceback
                traceback.print_exc()
            finally:
                self.after(0, self._on_fq_download_complete)

        self.download_thread = threading.Thread(target=download_thread_target_wrapper, daemon=True)
        self.download_thread.start()

    # 原独立设置窗口已移除，现在使用集成设置区域

    def on_closing(self):
        """窗口关闭事件处理"""
        if self.is_downloading:
            if messagebox.askyesno("确认", "下载任务正在进行中, 确定要退出吗?"):
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = NovelDownloaderGUI()
    center_window_on_screen(app)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
