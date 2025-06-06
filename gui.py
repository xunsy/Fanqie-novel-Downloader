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

# 设置 CustomTkinter 外观
ctk.set_default_color_theme(CONFIG.get("appearance", {}).get("color_theme", "blue"))

class NovelDownloaderGUI(ctk.CTk):
    """番茄小说下载器的主GUI窗口类"""
    
    def __init__(self):
        """初始化主窗口和应用程序状态"""
        super().__init__()

        # 基本窗口设置
        self.version = "1.7"
        self.title(f"🍅 番茄小说下载器 Pro v{self.version} - 智能下载引擎")

        # 设置现代化窗口大小
        self.geometry("1000x750")
        self.minsize(900, 650)

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

        self._setup_ui()

    def _setup_ui(self):
        """设置主窗口的用户界面布局和组件"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._setup_main_frame()
        self._setup_progress_frame()
        self._setup_log_frame()
        self._setup_bottom_frame()

    def _setup_main_frame(self):
        """设置包含输入字段和主要操作按钮的顶部框架"""
        # 创建带有渐变效果的主框架
        main_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["accent"]
        )
        main_frame.grid(row=0, column=0, padx=25, pady=25, sticky="ew")

        # 添加标题区域
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=4, padx=20, pady=(20, 10), sticky="ew")

        title_label = ctk.CTkLabel(
            title_frame,
            text="🚀 智能下载控制台",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["accent"]
        )
        title_label.pack(side="left")

        # 状态指示器
        self.connection_status = ctk.CTkLabel(
            title_frame,
            text="🟢 API已连接",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["success"]
        )
        self.connection_status.pack(side="right")

        # 配置网格权重，让输入框可以拉伸
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=0)  # 按钮列不拉伸

        # 第一行：小说ID输入和搜索按钮，右侧是开始下载按钮
        id_label = ctk.CTkLabel(
            main_frame,
            text="📚 小说ID:",
            anchor="w",
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        id_label.grid(row=1, column=0, padx=(20, 10), pady=15, sticky="w")

        self.novel_id = ctk.CTkEntry(
            main_frame,
            placeholder_text="🔍 输入小说ID或书名进行智能识别",
            height=40,
            corner_radius=10,
            border_width=2,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=13)
        )
        self.novel_id.grid(row=1, column=1, padx=(0, 15), pady=15, sticky="ew")

        self.search_button = ctk.CTkButton(
            main_frame,
            text="🔍 搜索",
            command=self.handle_search_button_click,
            width=90,
            height=40,
            corner_radius=10,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"],
            border_width=2,
            border_color=self.colors["accent"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.search_button.grid(row=1, column=2, padx=(0, 20), pady=15)

        self.download_button = ctk.CTkButton(
            main_frame,
            text="⚡ 开始下载",
            command=self.start_download,
            width=140,
            height=40,
            corner_radius=10,
            fg_color=self.colors["accent"],
            hover_color=self.colors["success"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.download_button.grid(row=1, column=3, padx=(0, 20), pady=15)

        # 第二行：保存路径输入和浏览按钮，右侧是停止下载按钮
        path_label = ctk.CTkLabel(
            main_frame,
            text="💾 保存路径:",
            anchor="w",
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        path_label.grid(row=2, column=0, padx=(20, 10), pady=15, sticky="w")

        self.save_path = ctk.CTkEntry(
            main_frame,
            placeholder_text="📁 选择文件保存位置",
            height=40,
            corner_radius=10,
            border_width=2,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=13)
        )
        self.save_path.grid(row=2, column=1, padx=(0, 15), pady=15, sticky="ew")

        # 从配置加载默认保存路径
        try:
            file_settings = CONFIG.get("file", {})
            if not isinstance(file_settings, dict):
                file_settings = {}
            default_path = file_settings.get("default_save_path", "downloads")
            self.save_path.insert(0, default_path)
        except Exception as e:
            print(f"加载默认保存路径时出错: {e}，使用默认值 'downloads'")
            self.save_path.insert(0, "downloads")

        browse_button = ctk.CTkButton(
            main_frame,
            text="📂 浏览",
            command=self.browse_folder,
            width=90,
            height=40,
            corner_radius=10,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"],
            border_width=2,
            border_color=self.colors["accent"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        browse_button.grid(row=2, column=2, padx=(0, 20), pady=15)

        self.stop_download_button = ctk.CTkButton(
            main_frame,
            text="⏹️ 停止下载",
            command=self._handle_stop_download_click,
            width=140,
            height=40,
            corner_radius=10,
            fg_color=self.colors["error"],
            hover_color="#cc3a47",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.stop_download_button.grid(row=2, column=3, padx=(0, 20), pady=15)

        # 第三行：输出格式选择
        format_label = ctk.CTkLabel(
            main_frame,
            text="📄 输出格式:",
            anchor="w",
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        format_label.grid(row=3, column=0, padx=(20, 10), pady=(15, 20), sticky="w")

        self.output_format = ctk.CTkSegmentedButton(
            main_frame,
            values=["📝 TXT", "📖 EPUB"],
            corner_radius=10,
            border_width=2,
            fg_color=self.colors["secondary"],
            selected_color=self.colors["accent"],
            selected_hover_color=self.colors["primary"],
            unselected_color=self.colors["surface"],
            unselected_hover_color=self.colors["secondary"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.output_format.grid(row=3, column=1, padx=(0, 15), pady=(15, 20), sticky="w")
        self.output_format.set("📝 TXT")

    def get_output_format(self):
        """获取选择的输出格式（去除图标）"""
        format_text = self.output_format.get()
        if "TXT" in format_text:
            return "TXT"
        elif "EPUB" in format_text:
            return "EPUB"
        return "TXT"  # 默认值

    def _setup_progress_frame(self):
        """设置显示下载进度条和状态标签的框架"""
        progress_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        progress_frame.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        # 进度标题
        progress_title = ctk.CTkLabel(
            progress_frame,
            text="📊 下载进度监控",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        progress_title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 进度条
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=25,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["secondary"],
            progress_color=self.colors["accent"]
        )
        self.progress_bar.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.progress_bar.set(0)

        # 状态标签
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="🚀 系统就绪 - 等待下载指令",
            anchor="center",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.colors["text"]
        )
        self.status_label.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        # 状态指示器框架
        status_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        status_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Tor状态标签
        tor_enabled = CONFIG.get("tor", {}).get("enabled", False)
        tor_status_text = "🔒 Tor: 已启用" if tor_enabled else "🔓 Tor: 已禁用"
        self.tor_status_label = ctk.CTkLabel(
            status_frame,
            text=tor_status_text,
            anchor="center",
            text_color=self.colors["success"] if tor_enabled else self.colors["warning"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.tor_status_label.grid(row=0, column=0, padx=10, pady=5)

        # API状态标签
        self.api_status_label = ctk.CTkLabel(
            status_frame,
            text="🌐 API: 已连接",
            anchor="center",
            text_color=self.colors["success"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.api_status_label.grid(row=0, column=1, padx=10, pady=5)

        # 速度显示标签
        self.speed_label = ctk.CTkLabel(
            status_frame,
            text="⚡ 速度: 待机中",
            anchor="center",
            text_color=self.colors["text_secondary"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.speed_label.grid(row=0, column=2, padx=10, pady=5)

    def _setup_log_frame(self):
        """设置包含日志输出文本框的框架"""
        log_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        log_frame.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        # 日志标题框架
        log_title_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        log_title_frame.grid_columnconfigure(0, weight=1)

        # 日志标题
        log_title = ctk.CTkLabel(
            log_title_frame,
            text="🔍 实时日志监控",
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        log_title.pack(side="left")

        # 日志状态指示器
        self.log_status = ctk.CTkLabel(
            log_title_frame,
            text="🟢 系统运行正常",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["success"]
        )
        self.log_status.pack(side="right")

        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            border_width=2,
            border_color=self.colors["surface"]
        )
        self.log_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_text.configure(state="disabled")

    def _setup_bottom_frame(self):
        """设置包含设置和清空日志按钮的底部框架"""
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, padx=25, pady=(0, 25), sticky="ew")
        bottom_frame.grid_columnconfigure(1, weight=1)  # 中间空间拉伸

        # 设置按钮（左侧）
        settings_button = ctk.CTkButton(
            bottom_frame,
            text="⚙️ 高级设置",
            command=self.open_settings,
            width=140,
            height=45,
            corner_radius=12,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["primary"],
            border_width=2,
            border_color=self.colors["accent"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_button.grid(row=0, column=0, padx=(0, 15), pady=10, sticky="w")

        # 版本信息标签（中间）
        version_label = ctk.CTkLabel(
            bottom_frame,
            text=f"🍅 番茄小说下载器 Pro v{self.version} | 智能下载引擎",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        version_label.grid(row=0, column=1, pady=10)

        # 清空日志按钮（右侧）
        clear_log_button = ctk.CTkButton(
            bottom_frame,
            text="🗑️ 清空日志",
            command=self.clear_log,
            width=140,
            height=45,
            corner_radius=12,
            fg_color=self.colors["warning"],
            hover_color="#e6940a",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        clear_log_button.grid(row=0, column=2, padx=(15, 0), pady=10, sticky="e")

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
            # 立即保存到配置文件
            if 'file' not in CONFIG:
                CONFIG['file'] = {}
            CONFIG['file']['default_save_path'] = folder_path
            save_user_config(CONFIG)

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
            save_path = CONFIG["file"].get("default_save_path", "downloads")

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

    def open_settings(self):
        """打开设置窗口"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("🔧 高级设置 - 番茄小说下载器 Pro")
        settings_window.geometry("700x800")
        settings_window.minsize(650, 750)
        settings_window.transient(self)
        settings_window.grab_set()
        center_window_over_parent(settings_window, self)

        # 创建主滚动框架
        main_frame = ctk.CTkScrollableFrame(
            settings_window,
            corner_radius=15,
            border_width=2,
            border_color=self.colors["accent"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 设置标题
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 30))

        title_label = ctk.CTkLabel(
            title_frame,
            text="⚙️ 系统配置中心",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["accent"]
        )
        title_label.pack(side="left")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="🚀 优化您的下载体验",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        subtitle_label.pack(side="right")

        # 1. 性能设置区域
        perf_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        perf_frame.pack(fill="x", padx=20, pady=(0, 20))

        perf_title = ctk.CTkLabel(
            perf_frame,
            text="⚡ 性能优化设置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        perf_title.pack(anchor="w", padx=20, pady=(20, 15))

        # 最大并发下载数
        workers_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        workers_frame.pack(fill="x", padx=20, pady=(0, 15))
        workers_frame.grid_columnconfigure(1, weight=1)

        workers_label = ctk.CTkLabel(
            workers_frame,
            text="🔄 最大并发下载数:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        workers_label.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")

        workers_var = tk.IntVar(value=CONFIG["request"].get("max_workers", 3))
        workers_slider = ctk.CTkSlider(
            workers_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=workers_var,
            progress_color=self.colors["accent"],
            button_color=self.colors["success"],
            button_hover_color=self.colors["primary"]
        )
        workers_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        workers_value_label = ctk.CTkLabel(
            workers_frame,
            textvariable=workers_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        workers_value_label.grid(row=0, column=2, padx=(20, 0), pady=5)
        workers_slider.configure(command=lambda v: workers_value_label.configure(text=str(int(v))))

        # 请求超时时间
        timeout_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        timeout_frame.pack(fill="x", padx=20, pady=(0, 15))
        timeout_frame.grid_columnconfigure(1, weight=1)

        timeout_label = ctk.CTkLabel(
            timeout_frame,
            text="⏱️ 请求超时时间 (秒):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        timeout_label.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")

        timeout_slider = ctk.CTkSlider(
            timeout_frame,
            from_=5,
            to=60,
            number_of_steps=11,
            variable=ctk.IntVar(value=CONFIG.get("request", {}).get("timeout", 10)),
            progress_color=self.colors["accent"],
            button_color=self.colors["success"],
            button_hover_color=self.colors["primary"]
        )
        timeout_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        timeout_value_label = ctk.CTkLabel(
            timeout_frame,
            text=str(timeout_slider.get()),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        timeout_value_label.grid(row=0, column=2, padx=(20, 0), pady=5)
        timeout_slider.configure(command=lambda v: timeout_value_label.configure(text=str(int(v))))

        # 请求速率限制
        rate_frame = ctk.CTkFrame(perf_frame, fg_color="transparent")
        rate_frame.pack(fill="x", padx=20, pady=(0, 20))
        rate_frame.grid_columnconfigure(1, weight=1)

        rate_limit_label = ctk.CTkLabel(
            rate_frame,
            text="🚀 请求速率限制 (次/秒):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        rate_limit_label.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")

        rate_limit_slider = ctk.CTkSlider(
            rate_frame,
            from_=0.1,
            to=5.0,
            number_of_steps=49,
            variable=ctk.DoubleVar(value=1/CONFIG.get("request", {}).get("request_rate_limit", 0.2) if CONFIG.get("request", {}).get("request_rate_limit", 0.2) > 0 else 5),
            progress_color=self.colors["accent"],
            button_color=self.colors["success"],
            button_hover_color=self.colors["primary"]
        )
        rate_limit_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        rate_limit_value_label = ctk.CTkLabel(
            rate_frame,
            text=f"{rate_limit_slider.get():.1f}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent"]
        )
        rate_limit_value_label.grid(row=0, column=2, padx=(20, 0), pady=5)
        rate_limit_slider.configure(command=lambda v: rate_limit_value_label.configure(text=f"{v:.1f}"))

        # 2. 输出设置区域
        output_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        output_frame.pack(fill="x", padx=20, pady=(0, 20))

        output_title = ctk.CTkLabel(
            output_frame,
            text="📄 输出格式设置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        output_title.pack(anchor="w", padx=20, pady=(20, 15))

        # EPUB自动生成选项
        generate_epub_var = ctk.BooleanVar(value=CONFIG.get("output", {}).get("generate_epub_when_txt_selected", False))
        generate_epub_check = ctk.CTkCheckBox(
            output_frame,
            text="📚 选择 TXT 格式时，也自动生成 EPUB 文件",
            variable=generate_epub_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        generate_epub_check.pack(anchor="w", padx=20, pady=(0, 20))

        # 3. Tor网络设置区域
        tor_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        tor_frame.pack(fill="x", padx=20, pady=(0, 20))

        tor_title = ctk.CTkLabel(
            tor_frame,
            text="🔒 Tor 网络代理设置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        tor_title.pack(anchor="w", padx=20, pady=(20, 15))

        # Tor启用开关
        tor_enabled_var = ctk.BooleanVar(value=CONFIG.get("tor", {}).get("enabled", False))
        tor_enabled_check = ctk.CTkCheckBox(
            tor_frame,
            text="🛡️ 启用 Tor 网络代理（增强隐私保护）",
            variable=tor_enabled_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        tor_enabled_check.pack(anchor="w", padx=20, pady=(0, 15))

        # Tor端口设置
        tor_port_frame = ctk.CTkFrame(tor_frame, fg_color="transparent")
        tor_port_frame.pack(fill="x", padx=20, pady=(0, 15))

        tor_port_label = ctk.CTkLabel(
            tor_port_frame,
            text="🔌 Tor 代理端口:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        tor_port_label.pack(side="left")

        tor_port_var = ctk.IntVar(value=CONFIG.get("tor", {}).get("proxy_port", 9050))
        tor_port_entry = ctk.CTkEntry(
            tor_port_frame,
            textvariable=tor_port_var,
            width=120,
            height=35,
            corner_radius=8,
            border_width=2,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=13)
        )
        tor_port_entry.pack(side="left", padx=(20, 0))

        # Tor连接测试按钮
        def test_tor_connection():
            try:
                # 临时更新配置进行测试
                old_enabled = CONFIG.get("tor", {}).get("enabled", False)
                old_port = CONFIG.get("tor", {}).get("proxy_port", 9050)

                CONFIG["tor"]["enabled"] = True
                CONFIG["tor"]["proxy_port"] = tor_port_var.get()

                # 导入Tor函数
                from downloader import check_tor_connection

                test_button.configure(text="测试中...", state="disabled")
                settings_window.update()

                if check_tor_connection():
                    messagebox.showinfo("Tor连接测试", "Tor连接成功！", parent=settings_window)
                else:
                    messagebox.showerror("Tor连接测试", "Tor连接失败！请检查Tor服务是否运行以及端口设置是否正确。", parent=settings_window)

                # 恢复原配置
                CONFIG["tor"]["enabled"] = old_enabled
                CONFIG["tor"]["proxy_port"] = old_port

            except Exception as e:
                messagebox.showerror("Tor连接测试", f"测试过程中出错: {str(e)}", parent=settings_window)
            finally:
                test_button.configure(text="测试连接", state="normal")

        test_button = ctk.CTkButton(
            tor_port_frame,
            text="🔍 测试连接",
            command=test_tor_connection,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=self.colors["accent"],
            hover_color=self.colors["success"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        test_button.pack(side="right", padx=(20, 0))

        # 4. Cloudflare Workers反代设置区域
        proxy_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["secondary"]
        )
        proxy_frame.pack(fill="x", padx=20, pady=(0, 20))

        proxy_title = ctk.CTkLabel(
            proxy_frame,
            text="🌐 Cloudflare Workers 反代设置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        proxy_title.pack(anchor="w", padx=20, pady=(20, 15))

        # 反代启用开关
        proxy_enabled_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("enabled", False))
        proxy_enabled_check = ctk.CTkCheckBox(
            proxy_frame,
            text="🚀 启用 Cloudflare Workers 反代（绕过网络限制）",
            variable=proxy_enabled_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        proxy_enabled_check.pack(anchor="w", padx=20, pady=(0, 15))

        # 反代域名设置
        proxy_domain_frame = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        proxy_domain_frame.pack(fill="x", padx=20, pady=(0, 15))

        proxy_domain_label = ctk.CTkLabel(
            proxy_domain_frame,
            text="🔗 反代域名:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        proxy_domain_label.pack(anchor="w", pady=(0, 8))

        proxy_domain_var = ctk.StringVar(value=CONFIG.get("cloudflare_proxy", {}).get("proxy_domain", ""))
        proxy_domain_entry = ctk.CTkEntry(
            proxy_domain_frame,
            textvariable=proxy_domain_var,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color=self.colors["secondary"],
            font=ctk.CTkFont(size=13),
            placeholder_text="🌐 例如: your-worker.your-subdomain.workers.dev"
        )
        proxy_domain_entry.pack(fill="x", pady=(0, 10))

        # 回退到原始URL选项
        fallback_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("fallback_to_original", True))
        fallback_check = ctk.CTkCheckBox(
            proxy_frame,
            text="🔄 反代失败时自动回退到原始URL",
            variable=fallback_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            checkmark_color=self.colors["text"]
        )
        fallback_check.pack(anchor="w", padx=20, pady=(0, 15))

        # 测试反代连接按钮
        def test_cloudflare_proxy():
            proxy_domain = proxy_domain_var.get().strip()
            if not proxy_domain:
                messagebox.showwarning("警告", "请先输入反代域名", parent=settings_window)
                return

            try:
                # 临时更新配置进行测试
                old_enabled = CONFIG.get("cloudflare_proxy", {}).get("enabled", False)
                old_domain = CONFIG.get("cloudflare_proxy", {}).get("proxy_domain", "")

                if "cloudflare_proxy" not in CONFIG:
                    CONFIG["cloudflare_proxy"] = {}
                CONFIG["cloudflare_proxy"]["enabled"] = True
                CONFIG["cloudflare_proxy"]["proxy_domain"] = proxy_domain

                # 导入测试函数
                from downloader import test_cloudflare_proxy

                proxy_test_button.configure(text="测试中...", state="disabled")
                settings_window.update()

                if test_cloudflare_proxy():
                    messagebox.showinfo("反代连接测试", "Cloudflare Workers反代连接成功！", parent=settings_window)
                else:
                    messagebox.showerror("反代连接测试", "反代连接失败！请检查域名是否正确以及Workers脚本是否部署。", parent=settings_window)

                # 恢复原配置
                CONFIG["cloudflare_proxy"]["enabled"] = old_enabled
                CONFIG["cloudflare_proxy"]["proxy_domain"] = old_domain

            except Exception as e:
                messagebox.showerror("反代连接测试", f"测试过程中出错: {str(e)}", parent=settings_window)
            finally:
                proxy_test_button.configure(text="测试连接", state="normal")

        proxy_test_button = ctk.CTkButton(
            proxy_domain_frame,
            text="🔍 测试反代连接",
            command=test_cloudflare_proxy,
            width=150,
            height=40,
            corner_radius=10,
            fg_color=self.colors["accent"],
            hover_color=self.colors["success"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        proxy_test_button.pack(anchor="e", pady=(0, 5))

        # 保存和取消按钮区域
        button_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=2,
            border_color=self.colors["accent"]
        )
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        button_title = ctk.CTkLabel(
            button_frame,
            text="💾 保存配置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["accent"]
        )
        button_title.pack(pady=(20, 15))

        # 将控件打包传递给保存函数
        controls_to_save = {
            'sliders': {
                'threads': workers_slider,
                'timeout': timeout_slider,
                'rate_limit': rate_limit_slider
            },
            'path_entry': self.save_path,
            'check_var': generate_epub_var,
            'tor_enabled_var': tor_enabled_var,
            'tor_port_var': tor_port_var,
            'proxy_enabled_var': proxy_enabled_var,
            'proxy_domain_var': proxy_domain_var,
            'fallback_var': fallback_var
        }

        from functools import partial
        save_command = partial(self._save_settings_wrapper, settings_window, controls_to_save)

        # 按钮容器
        buttons_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_container.pack(pady=(0, 20))

        save_button = ctk.CTkButton(
            buttons_container,
            text="✅ 保存设置",
            command=save_command,
            width=150,
            height=45,
            corner_radius=12,
            fg_color=self.colors["success"],
            hover_color="#00cc77",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        save_button.pack(side="left", padx=15)

        cancel_button = ctk.CTkButton(
            buttons_container,
            text="❌ 取消",
            command=settings_window.destroy,
            width=150,
            height=45,
            corner_radius=12,
            fg_color=self.colors["error"],
            hover_color="#cc3a47",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        cancel_button.pack(side="left", padx=15)

    def _save_settings_wrapper(self, settings_window, controls):
        """保存设置的包装函数"""
        try:
            sliders = controls['sliders']
            path_entry = controls['path_entry']
            check_var = controls['check_var']
            tor_enabled_var = controls['tor_enabled_var']
            tor_port_var = controls['tor_port_var']

            # 获取旧的默认路径用于比较
            try:
                file_settings = CONFIG.get("file", {})
                if not isinstance(file_settings, dict):
                    file_settings = {}
                old_default_path = file_settings.get("default_save_path", "downloads")
            except Exception:
                old_default_path = "downloads"

            # 更新全局CONFIG
            if "download" not in CONFIG: CONFIG["download"] = {}
            if "request" not in CONFIG: CONFIG["request"] = {}
            if "file" not in CONFIG: CONFIG["file"] = {}
            if "tor" not in CONFIG: CONFIG["tor"] = {}
            if "cloudflare_proxy" not in CONFIG: CONFIG["cloudflare_proxy"] = {}

            CONFIG["request"]["max_workers"] = int(sliders['threads'].get())
            CONFIG["request"]["timeout"] = int(sliders['timeout'].get())

            # 将次数/秒转换为秒/次
            requests_per_second = sliders['rate_limit'].get()
            CONFIG["request"]["request_rate_limit"] = 1 / requests_per_second if requests_per_second > 0 else 0

            new_default_path = path_entry.get().strip()
            CONFIG["file"]["default_save_path"] = new_default_path
            CONFIG["output"]["generate_epub_when_txt_selected"] = check_var.get()

            # 保存Tor设置
            CONFIG["tor"]["enabled"] = tor_enabled_var.get()
            CONFIG["tor"]["proxy_port"] = tor_port_var.get()

            # 保存Cloudflare Workers反代设置
            CONFIG["cloudflare_proxy"]["enabled"] = controls['proxy_enabled_var'].get()
            CONFIG["cloudflare_proxy"]["proxy_domain"] = controls['proxy_domain_var'].get().strip()
            CONFIG["cloudflare_proxy"]["fallback_to_original"] = controls['fallback_var'].get()

            # 调用保存配置函数
            if save_user_config(CONFIG):
                current_main_path = self.save_path.get().strip()
                if not current_main_path or current_main_path == old_default_path:
                    self.save_path.delete(0, "end")
                    self.save_path.insert(0, new_default_path)

                # 更新Tor状态显示
                self.update_tor_status()

                messagebox.showinfo("成功", "设置已成功保存！", parent=settings_window)
                settings_window.destroy()
            else:
                messagebox.showerror("错误", "保存设置失败，请检查 user_config.json 文件权限或路径。", parent=settings_window)

        except Exception as e:
            messagebox.showerror("保存错误", f"保存设置时发生错误: {e}", parent=settings_window)
            traceback.print_exc()

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
