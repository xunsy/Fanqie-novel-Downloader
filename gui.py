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
    from utils import center_window_over_parent, center_window_on_screen, resource_path, generate_epub, EBOOKLIB_AVAILABLE
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
        self.version = "1.3.0"
        self.title(f"番茄小说下载器 v{self.version}")
        
        # 从配置加载窗口大小
        try:
            window_settings = CONFIG.get("window", {})
            if not isinstance(window_settings, dict):
                window_settings = {}
            default_geometry = window_settings.get("default_geometry", "800x600")
            self.geometry(default_geometry)
        except Exception as e:
            print(f"加载窗口几何尺寸时出错: {e}，使用默认值 800x600")
            self.geometry("800x600")

        # 状态变量
        self.is_downloading = False
        self.downloaded_chapters = set()
        self.download_thread: Optional[threading.Thread] = None
        self.current_fq_downloader: Optional[GUIdownloader] = None

        self.load_icons()
        self._setup_ui()

    def load_icons(self):
        """加载应用程序所需的图标文件"""
        self.icons = {}
        icon_size = (20, 20)
        assets_path = resource_path("assets")
        print(f"图标资源路径: {assets_path}")
        
        try:
            from PIL import Image, ImageTk
            icon_files = {
                "settings": "settings.png",
                "search": "search.png",
                "folder": "folder.png",
                "download": "download.png"
            }

            for name, file in icon_files.items():
                icon_path = os.path.join(assets_path, file)
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path).resize(icon_size)
                        setattr(self, f"_img_{name}", img)
                        self.icons[name] = ctk.CTkImage(light_image=img, dark_image=img, size=icon_size)
                        print(f"成功加载图标: {name}")
                    except Exception as e:
                        print(f"无法加载图标 {file}: {e}")
                        self.icons[name] = None
                else:
                    print(f"图标文件未找到: {icon_path}")
                    self.icons[name] = None
        except ImportError as e:
            print(f"警告: PIL (Pillow) 模块加载失败，无法加载图标。请运行 'pip install Pillow'。错误: {e}")

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
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # 配置网格权重，让输入框可以拉伸
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=0)  # 按钮列不拉伸

        # 第一行：小说ID输入和搜索按钮，右侧是开始下载按钮
        id_label = ctk.CTkLabel(main_frame, text="小说ID:", anchor="w", width=80)
        id_label.grid(row=0, column=0, padx=(10, 10), pady=12, sticky="w")

        self.novel_id = ctk.CTkEntry(main_frame, placeholder_text="输入小说ID或书名")
        self.novel_id.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="ew")

        search_icon = self.icons.get("search")
        self.search_button = ctk.CTkButton(
            main_frame, text="搜索", command=self.handle_search_button_click, width=80,
            image=search_icon, compound="left" if search_icon else "none"
        )
        self.search_button.grid(row=0, column=2, padx=(0, 20), pady=12)

        download_icon = self.icons.get("download")
        self.download_button = ctk.CTkButton(
            main_frame, text="开始下载", command=self.start_download, width=120,
            image=download_icon, compound="left" if download_icon else "none"
        )
        self.download_button.grid(row=0, column=3, padx=(0, 10), pady=12)

        # 第二行：保存路径输入和浏览按钮，右侧是停止下载按钮
        path_label = ctk.CTkLabel(main_frame, text="保存路径:", anchor="w", width=80)
        path_label.grid(row=1, column=0, padx=(10, 10), pady=12, sticky="w")

        self.save_path = ctk.CTkEntry(main_frame, placeholder_text="选择保存位置")
        self.save_path.grid(row=1, column=1, padx=(0, 10), pady=12, sticky="ew")

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

        folder_icon = self.icons.get("folder")
        browse_button = ctk.CTkButton(
            main_frame, text="浏览", command=self.browse_folder, width=80,
            image=folder_icon, compound="left" if folder_icon else "none"
        )
        browse_button.grid(row=1, column=2, padx=(0, 20), pady=12)

        self.stop_download_button = ctk.CTkButton(
            main_frame, text="停止下载", command=self._handle_stop_download_click, width=120,
            state="disabled"
        )
        self.stop_download_button.grid(row=1, column=3, padx=(0, 10), pady=12)

        # 第三行：输出格式选择
        format_label = ctk.CTkLabel(main_frame, text="输出格式:", anchor="w", width=80)
        format_label.grid(row=2, column=0, padx=(10, 10), pady=12, sticky="w")

        self.output_format = ctk.CTkSegmentedButton(main_frame, values=["TXT", "EPUB"])
        self.output_format.grid(row=2, column=1, padx=(0, 10), pady=12, sticky="w")
        self.output_format.set("TXT")

    def _setup_progress_frame(self):
        """设置显示下载进度条和状态标签的框架"""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        # 进度条
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.progress_bar.set(0)

        # 状态标签
        self.status_label = ctk.CTkLabel(progress_frame, text="准备就绪", anchor="center",
                                       font=ctk.CTkFont(size=14))
        self.status_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        # Tor状态标签
        tor_enabled = CONFIG.get("tor", {}).get("enabled", False)
        tor_status_text = "🔒 Tor: 已启用" if tor_enabled else "🔓 Tor: 已禁用"
        self.tor_status_label = ctk.CTkLabel(progress_frame, text=tor_status_text, anchor="center",
                                           text_color="green" if tor_enabled else "orange",
                                           font=ctk.CTkFont(size=12))
        self.tor_status_label.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

    def _setup_log_frame(self):
        """设置包含日志输出文本框的框架"""
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        # 日志标题
        log_title = ctk.CTkLabel(log_frame, text="📋 下载日志", anchor="w",
                               font=ctk.CTkFont(size=14, weight="bold"))
        log_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        # 日志文本框
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", font=ctk.CTkFont(size=12))
        self.log_text.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.log_text.configure(state="disabled")

    def _setup_bottom_frame(self):
        """设置包含设置和清空日志按钮的底部框架"""
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(1, weight=1)  # 中间空间拉伸

        # 设置按钮（左侧）
        settings_icon = self.icons.get("settings")
        settings_button = ctk.CTkButton(
            bottom_frame, text="设置", command=self.open_settings, width=120,
            image=settings_icon, compound="left" if settings_icon else "none"
        )
        settings_button.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

        # 清空日志按钮（右侧）
        clear_log_button = ctk.CTkButton(
            bottom_frame, text="清空日志", command=self.clear_log, width=120
        )
        clear_log_button.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="e")

    def log(self, message: str):
        """向日志文本框添加一条消息"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def update_progress(self, value: float, status_text: str):
        """更新进度条和状态标签"""
        self.progress_var.set(value)
        self.progress_bar.set(value / 100)
        self.status_label.configure(text=status_text)
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
        self.log(f"搜索功能暂未实现，输入内容: {input_text}")
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
        settings_window.title("设置")
        settings_window.minsize(450, 350)
        settings_window.transient(self)
        settings_window.grab_set()
        center_window_over_parent(settings_window, self)

        # 创建设置框架
        frame = ctk.CTkFrame(settings_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. 最大并发下载数
        workers_label = ctk.CTkLabel(frame, text="最大并发下载数:", anchor="w")
        workers_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        workers_var = tk.IntVar(value=CONFIG["request"].get("max_workers", 3))
        workers_slider = ctk.CTkSlider(frame, from_=1, to=10, number_of_steps=9, variable=workers_var)
        workers_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        workers_value_label = ctk.CTkLabel(frame, textvariable=workers_var)
        workers_value_label.grid(row=0, column=2, padx=10, pady=10)
        workers_slider.configure(command=lambda v: workers_value_label.configure(text=str(int(v))))

        # 2. 请求超时时间
        timeout_label = ctk.CTkLabel(frame, text="请求超时时间 (秒):")
        timeout_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        timeout_slider = ctk.CTkSlider(frame, from_=5, to=60, number_of_steps=11,
                                       variable=ctk.IntVar(value=CONFIG.get("request", {}).get("timeout", 10)))
        timeout_slider.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        timeout_value_label = ctk.CTkLabel(frame, text=str(timeout_slider.get()))
        timeout_value_label.grid(row=1, column=2, padx=10, pady=10)
        timeout_slider.configure(command=lambda v: timeout_value_label.configure(text=str(int(v))))

        # 3. 请求速率限制
        rate_limit_label = ctk.CTkLabel(frame, text="请求速率限制 (次/秒):")
        rate_limit_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        rate_limit_slider = ctk.CTkSlider(frame, from_=0.1, to=5.0, number_of_steps=49,
                                          variable=ctk.DoubleVar(value=1/CONFIG.get("request", {}).get("request_rate_limit", 0.2) if CONFIG.get("request", {}).get("request_rate_limit", 0.2) > 0 else 5))
        rate_limit_slider.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        rate_limit_value_label = ctk.CTkLabel(frame, text=f"{rate_limit_slider.get():.1f}")
        rate_limit_value_label.grid(row=2, column=2, padx=10, pady=10)
        rate_limit_slider.configure(command=lambda v: rate_limit_value_label.configure(text=f"{v:.1f}"))

        # 4. 选择TXT时也生成EPUB
        generate_epub_var = ctk.BooleanVar(value=CONFIG.get("output", {}).get("generate_epub_when_txt_selected", False))
        generate_epub_check = ctk.CTkCheckBox(frame, text="选择 TXT 格式时，也自动生成 EPUB 文件",
                                              variable=generate_epub_var)
        generate_epub_check.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # 5. Tor网络设置
        tor_frame = ctk.CTkFrame(frame)
        tor_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        tor_frame.grid_columnconfigure(1, weight=1)

        # Tor启用开关
        tor_enabled_var = ctk.BooleanVar(value=CONFIG.get("tor", {}).get("enabled", False))
        tor_enabled_check = ctk.CTkCheckBox(tor_frame, text="启用 Tor 网络代理",
                                            variable=tor_enabled_var)
        tor_enabled_check.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Tor端口设置
        tor_port_label = ctk.CTkLabel(tor_frame, text="Tor 代理端口:")
        tor_port_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        tor_port_var = ctk.IntVar(value=CONFIG.get("tor", {}).get("proxy_port", 9050))
        tor_port_entry = ctk.CTkEntry(tor_frame, textvariable=tor_port_var, width=100)
        tor_port_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

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

        test_button = ctk.CTkButton(tor_frame, text="测试连接", command=test_tor_connection, width=100)
        test_button.grid(row=1, column=2, padx=10, pady=5)

        # 6. Cloudflare Workers反代设置
        proxy_frame = ctk.CTkFrame(frame)
        proxy_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        proxy_frame.grid_columnconfigure(1, weight=1)

        # 反代启用开关
        proxy_enabled_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("enabled", False))
        proxy_enabled_check = ctk.CTkCheckBox(proxy_frame, text="启用 Cloudflare Workers 反代",
                                              variable=proxy_enabled_var)
        proxy_enabled_check.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # 反代域名设置
        proxy_domain_label = ctk.CTkLabel(proxy_frame, text="反代域名:")
        proxy_domain_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        proxy_domain_var = ctk.StringVar(value=CONFIG.get("cloudflare_proxy", {}).get("proxy_domain", ""))
        proxy_domain_entry = ctk.CTkEntry(proxy_frame, textvariable=proxy_domain_var, width=300,
                                          placeholder_text="例如: your-worker.your-subdomain.workers.dev")
        proxy_domain_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # 回退到原始URL选项
        fallback_var = ctk.BooleanVar(value=CONFIG.get("cloudflare_proxy", {}).get("fallback_to_original", True))
        fallback_check = ctk.CTkCheckBox(proxy_frame, text="反代失败时回退到原始URL",
                                         variable=fallback_var)
        fallback_check.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="w")

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

        proxy_test_button = ctk.CTkButton(proxy_frame, text="测试连接", command=test_cloudflare_proxy, width=100)
        proxy_test_button.grid(row=1, column=2, padx=10, pady=5)

        # 保存和取消按钮
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)

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

        save_button = ctk.CTkButton(button_frame, text="保存设置", command=save_command)
        save_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="取消", command=settings_window.destroy)
        cancel_button.pack(side="left", padx=10)

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
