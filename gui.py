# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
from api import TomatoAPI
import threading
import os
import json
import re
from datetime import datetime

class BeautifulApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 获取屏幕尺寸并设置窗口
        self.setup_window()
        
        # 现代化浅色主题
        self.colors = {
            'bg_primary': '#f8f9fa',       # 主背景 - 浅灰白
            'bg_secondary': '#ffffff',     # 次要背景 - 纯白
            'bg_card': '#ffffff',          # 卡片背景 - 纯白
            'accent': '#0066cc',           # 强调色 - 蓝色
            'accent_hover': '#0052a3',     # 悬停强调色 - 深蓝
            'accent_light': '#e3f2fd',     # 浅蓝背景
            'text_primary': '#2c3e50',     # 主要文字 - 深灰
            'text_secondary': '#6c757d',   # 次要文字 - 中灰
            'text_muted': '#adb5bd',       # 弱化文字 - 浅灰
            'border': '#e9ecef',           # 边框色 - 浅灰
            'border_focus': '#80bdff',     # 聚焦边框 - 蓝色
            'success': '#28a745',          # 成功色 - 绿色
            'warning': '#ffc107',          # 警告色 - 黄色
            'error': '#dc3545',            # 错误色 - 红色
            'shadow': '#00000010'          # 阴影色
        }
        
        # 设置主窗口样式
        self.configure(bg=self.colors['bg_primary'])
        
        # 初始化API
        self.api = TomatoAPI()
        
        # 下载状态控制
        self.is_downloading = False
        
        # 创建自定义样式
        self.setup_styles()
        
        # 创建主界面
        self.create_widgets()

        # 绑定快捷键
        self.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.bind('<Return>', lambda e: self.search_books() if self.search_entry.focus_get() == self.search_entry else None)
        self.bind('<Escape>', lambda e: self.search_entry.delete(0, tk.END))

        # 启动时检查更新（后台进行）
        threading.Thread(target=self.check_updates_on_startup, daemon=True).start()

    def setup_window(self):
        """设置窗口尺寸和位置，自动适配屏幕"""
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 设置窗口为屏幕的75%，但不超过合理的最大值
        window_width = min(int(screen_width * 0.75), 1400)
        window_height = min(int(screen_height * 0.75), 900)
        
        # 设置最小尺寸
        min_width = min(300, int(screen_width * 0.6))
        min_height = min(700, int(screen_height * 0.6))
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(min_width, min_height)
        self.title("🍅 番茄小说下载器 - 现代版")

    def setup_styles(self):
        """设置现代化的浅色主题样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置卡片样式的LabelFrame
        style.configure('Card.TLabelframe', 
                       background=self.colors['bg_card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'])
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 12, 'bold'))
        
        # 配置现代化Entry样式
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=2,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       foreground=self.colors['text_primary'],
                       insertcolor=self.colors['accent'],
                       font=('Segoe UI', 11))
        style.map('Modern.TEntry',
                 bordercolor=[('focus', self.colors['border_focus'])])
        
        # 配置现代化Button样式
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(20, 10))
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        # 配置次要Button样式
        style.configure('Secondary.TButton',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       bordercolor=self.colors['border'],
                       focuscolor='none',
                       font=('Segoe UI', 10),
                       padding=(15, 8))
        style.map('Secondary.TButton',
                 background=[('active', self.colors['accent_light']),
                           ('pressed', self.colors['accent_light'])])
        
        # 配置现代化Treeview样式
        style.configure('Modern.Treeview',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=1,
                       bordercolor=self.colors['border'],
                       font=('Segoe UI', 10))
        style.configure('Modern.Treeview.Heading',
                       background=self.colors['accent_light'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 11, 'bold'),
                       borderwidth=1,
                       bordercolor=self.colors['border'])
        style.map('Modern.Treeview',
                 background=[('selected', self.colors['accent_light'])])
        
        # 配置进度条样式
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])

    def create_widgets(self):
        """创建现代化的界面组件"""
        # 创建主容器
        main_container = tk.Frame(self, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 顶部标题区域
        self.create_header(main_container)
        
        # 创建左右分栏的主要内容区域
        content_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # 左侧面板 - 搜索和结果
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 右侧面板 - 下载和日志
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # 创建各个功能区域
        self.create_search_section(left_panel)
        self.create_results_section(left_panel)
        self.create_download_section(right_panel)
        self.create_log_section(right_panel)
        
        # 底部状态栏
        self.create_status_bar(main_container)

    def create_header(self, parent):
        """创建顶部标题区域"""
        header_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # 主标题
        title_label = tk.Label(header_frame, 
                              text="🍅 番茄小说下载器",
                              font=('Segoe UI', 28, 'bold'),
                              fg=self.colors['accent'],
                              bg=self.colors['bg_primary'])
        title_label.pack(side='left')
        
        # 副标题
        subtitle_label = tk.Label(header_frame,
                                 text="现代化界面 · 智能下载 · 完美体验",
                                 font=('Segoe UI', 14),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_primary'])
        subtitle_label.pack(side='left', padx=(20, 0), pady=(8, 0))
        
        # 版本信息
        version_label = tk.Label(header_frame,
                                text="v2.1",
                                font=('Segoe UI', 12),
                                fg=self.colors['text_muted'],
                                bg=self.colors['bg_primary'])
        version_label.pack(side='right', pady=(8, 0))

    def create_search_section(self, parent):
        """创建搜索区域"""
        search_frame = ttk.LabelFrame(parent, text="📚 书籍搜索", style='Card.TLabelframe')
        search_frame.pack(fill='x', pady=(0, 15))
        
        # 搜索容器
        search_container = tk.Frame(search_frame, bg=self.colors['bg_card'])
        search_container.pack(fill='x', padx=20, pady=20)
        
        # 搜索提示
        hint_label = tk.Label(search_container,
                             text="输入书名或作者名进行搜索",
                             font=('Segoe UI', 10),
                             fg=self.colors['text_muted'],
                             bg=self.colors['bg_card'])
        hint_label.pack(anchor='w', pady=(0, 8))
        
        # 搜索输入框和按钮
        search_input_frame = tk.Frame(search_container, bg=self.colors['bg_card'])
        search_input_frame.pack(fill='x')
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_input_frame, 
                                     textvariable=self.search_var, 
                                     style='Modern.TEntry')
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=8)
        
        search_button = ttk.Button(search_input_frame, 
                                  text="🔍 搜索", 
                                  command=self.search_books,
                                  style='Accent.TButton')
        search_button.pack(side='right', padx=(15, 0))
        
        # 快捷操作提示
        shortcut_label = tk.Label(search_container,
                                 text="快捷键: Ctrl+F 聚焦搜索框, Enter 执行搜索, Esc 清空",
                                 font=('Segoe UI', 9),
                                 fg=self.colors['text_muted'],
                                 bg=self.colors['bg_card'])
        shortcut_label.pack(anchor='w', pady=(8, 0))

    def create_results_section(self, parent):
        """创建搜索结果区域"""
        results_frame = ttk.LabelFrame(parent, text="📖 搜索结果", style='Card.TLabelframe')
        results_frame.pack(fill='both', expand=True)

        # 结果容器
        results_container = tk.Frame(results_frame, bg=self.colors['bg_card'])
        results_container.pack(fill='both', expand=True, padx=20, pady=20)

        # 结果统计
        self.results_info_var = tk.StringVar(value="等待搜索...")
        results_info_label = tk.Label(results_container,
                                     textvariable=self.results_info_var,
                                     font=('Segoe UI', 10),
                                     fg=self.colors['text_secondary'],
                                     bg=self.colors['bg_card'])
        results_info_label.pack(anchor='w', pady=(0, 10))

        # 创建Treeview
        self.tree = ttk.Treeview(results_container,
                                columns=("ID", "Title", "Author"),
                                show="headings",
                                style='Modern.Treeview',
                                height=12)

        # 配置列
        self.tree.heading("ID", text="📋 书籍ID")
        self.tree.column("ID", width=120, anchor="center")
        self.tree.heading("Title", text="📚 书名")
        self.tree.column("Title", width=300)
        self.tree.heading("Author", text="✍️ 作者")
        self.tree.column("Author", width=150)

        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<Double-1>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.on_tree_click)

    def create_download_section(self, parent):
        """创建下载控制区域"""
        download_frame = ttk.LabelFrame(parent, text="⬇️ 下载控制", style='Card.TLabelframe')
        download_frame.pack(fill='x', pady=(0, 15))

        # 下载容器 - 保存为类属性以便其他方法访问
        self.download_container = tk.Frame(download_frame, bg=self.colors['bg_card'])
        self.download_container.pack(fill='x', padx=20, pady=20)

        # 书籍ID输入
        id_label = tk.Label(self.download_container,
                           text="书籍ID:",
                           font=('Segoe UI', 11, 'bold'),
                           fg=self.colors['text_primary'],
                           bg=self.colors['bg_card'])
        id_label.pack(anchor='w', pady=(0, 5))

        id_input_frame = tk.Frame(self.download_container, bg=self.colors['bg_card'])
        id_input_frame.pack(fill='x', pady=(0, 15))

        self.book_id_var = tk.StringVar()
        id_entry = ttk.Entry(id_input_frame,
                            textvariable=self.book_id_var,
                            style='Modern.TEntry',
                            font=('Segoe UI', 11))
        id_entry.pack(side='left', fill='x', expand=True, ipady=8)

        # 下载按钮
        download_button = ttk.Button(id_input_frame,
                                    text="📥 开始下载",
                                    command=self.download_book,
                                    style='Accent.TButton')
        download_button.pack(side='right', padx=(15, 0))

        # 进度变量
        self.progress_var = tk.DoubleVar()
        self.progress_text_var = tk.StringVar(value="等待下载...")
        
        # 进度条容器和进度条将在show_progress方法中创建

        # 当前下载信息
        self.current_book_var = tk.StringVar(value="")
        current_book_label = tk.Label(self.download_container,
                                     textvariable=self.current_book_var,
                                     font=('Segoe UI', 10),
                                     fg=self.colors['text_primary'],
                                     bg=self.colors['bg_card'],
                                     wraplength=300)
        current_book_label.pack(anchor='w', pady=(10, 0))

    def create_log_section(self, parent):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(parent, text="📝 下载日志", style='Card.TLabelframe')
        log_frame.pack(fill='both', expand=True)

        # 日志容器
        log_container = tk.Frame(log_frame, bg=self.colors['bg_card'])
        log_container.pack(fill='both', expand=True, padx=20, pady=20)

        # 日志工具栏
        log_toolbar = tk.Frame(log_container, bg=self.colors['bg_card'])
        log_toolbar.pack(fill='x', pady=(0, 10))

        clear_button = ttk.Button(log_toolbar,
                                 text="🗑️ 清空日志",
                                 command=self.clear_log,
                                 style='Secondary.TButton')
        clear_button.pack(side='right')

        log_info_label = tk.Label(log_toolbar,
                                 text="实时下载日志:",
                                 font=('Segoe UI', 10, 'bold'),
                                 fg=self.colors['text_primary'],
                                 bg=self.colors['bg_card'])
        log_info_label.pack(side='left')

        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_container,
                                                 wrap=tk.WORD,
                                                 bg=self.colors['bg_secondary'],
                                                 fg=self.colors['text_primary'],
                                                 font=('Consolas', 10),
                                                 borderwidth=1,
                                                 relief='solid',
                                                 insertbackground=self.colors['accent'])
        self.log_text.pack(fill='both', expand=True)

    def create_status_bar(self, parent):
        """创建底部状态栏"""
        self.status_bar = tk.Frame(parent, bg=self.colors['bg_secondary'], height=300)
        self.status_bar.pack(fill='x', pady=(20, 0))

        # 状态信息
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(self.status_bar,
                               textvariable=self.status_var,
                               font=('Segoe UI', 9),
                               fg=self.colors['text_secondary'],
                               bg=self.colors['bg_secondary'])
        status_label.pack(side='left', padx=10, pady=5)

        # 时间显示
        self.time_var = tk.StringVar()
        time_label = tk.Label(self.status_bar,
                             textvariable=self.time_var,
                             font=('Segoe UI', 9),
                             fg=self.colors['text_muted'],
                             bg=self.colors['bg_secondary'])
        time_label.pack(side='right', padx=10, pady=5)

        # 更新时间
        self.update_time()

    def update_time(self):
        """更新状态栏时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.after(300, self.update_time)

    def log(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            self.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空", "INFO")

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)

    def show_progress(self, show=True):
        """显示或隐藏进度条"""
        if show:
            # 确保进度容器已创建
            if not hasattr(self, 'progress_container') or not self.progress_container.winfo_exists():
                self.progress_container = tk.Frame(self.download_container, bg=self.colors['bg_card'])
                self.progress_bar = ttk.Progressbar(self.progress_container,
                                                  variable=self.progress_var,
                                                  style='Modern.Horizontal.TProgressbar',
                                                  mode='determinate')
            
            self.progress_container.pack(fill='x', pady=(0, 10))
            self.progress_bar.pack(fill='x', pady=(0, 5))
        else:
            if hasattr(self, 'progress_container') and self.progress_container.winfo_exists():
                self.progress_container.pack_forget()

    def update_progress(self, value, text=""):
        """更新进度条"""
        self.progress_var.set(value)
        if text:
            self.progress_text_var.set(text)
        self.update_idletasks()

    def search_books(self):
        """搜索书籍"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning("⚠️ 警告", "请输入搜索关键词")
            self.search_entry.focus()
            return

        self.log(f"🔍 开始搜索: {keyword}", "INFO")
        self.update_status("正在搜索...")
        self.results_info_var.set("搜索中...")

        # 清除之前的结果
        for i in self.tree.get_children():
            self.tree.delete(i)

        threading.Thread(target=self._search_worker, args=(keyword,), daemon=True).start()

    def _search_worker(self, keyword):
        """搜索工作线程"""
        try:
            search_results = self.api.search(keyword)

            if search_results and 'data' in search_results and 'search_tabs' in search_results['data'] and search_results['data']['search_tabs']:
                all_books = []
                search_tabs_data = search_results['data']['search_tabs']
                
                # 正确处理搜索结果结构
                if isinstance(search_tabs_data, list) and len(search_tabs_data) > 0:
                    # 获取第一个标签页的数据（通常是"综合"标签）
                    first_tab = search_tabs_data[0]
                    if 'data' in first_tab and isinstance(first_tab['data'], list):
                        for item in first_tab['data']:
                            if 'book_data' in item and item['book_data']:
                                # 处理book_data可能是列表或字典的情况
                                book_data = item['book_data']
                                if isinstance(book_data, list) and len(book_data) > 0:
                                    book = book_data[0]
                                else:
                                    book = book_data
                                
                                # 确保book_id存在
                                if 'book_id' not in book and 'book_id' in item:
                                    book['book_id'] = item['book_id']
                                
                                # 只添加小说类型的书籍，过滤掉听书类型
                                book_type = book.get('book_type')
                                # 检查book_type是否为1（听书），可能是字符串'1'或整数1
                                if str(book_type) != '1':  # book_type=1 是听书
                                    all_books.append(book)

                if not all_books:
                    self.log("❌ 未找到相关书籍", "WARNING")
                    self.results_info_var.set("未找到相关书籍")
                    self.update_status("搜索完成 - 无结果")
                    messagebox.showinfo("📚 搜索结果", "未找到相关书籍，请尝试其他关键词")
                else:
                    for book in all_books:
                        self.tree.insert("", "end", values=(
                            book.get('book_id', 'N/A'),
                            book.get('book_name', 'N/A'),
                            book.get('author', 'N/A')
                        ))

                    self.log(f"✅ 搜索完成，找到 {len(all_books)} 本书籍", "SUCCESS")
                    self.results_info_var.set(f"找到 {len(all_books)} 本相关书籍")
                    self.update_status("搜索完成")
            else:
                self.log("❌ 搜索失败或服务器无响应", "ERROR")
                self.results_info_var.set("搜索失败")
                self.update_status("搜索失败")
                messagebox.showerror("❌ 搜索失败", "搜索失败，请检查网络连接或稍后重试")

        except Exception as e:
            self.log(f"❌ 搜索出错: {str(e)}", "ERROR")
            self.results_info_var.set("搜索出错")
            self.update_status("搜索出错")
            messagebox.showerror("❌ 错误", f"搜索出错: {str(e)}")

    def on_tree_click(self, event):
        """处理树形视图单击事件"""
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            if values and len(values) >= 3:
                book_id = values[0]
                book_title = values[1]
                self.book_id_var.set(book_id)
                self.log(f"📋 选择了书籍: {book_title} (ID: {book_id})", "INFO")

    def on_tree_select(self, event):
        """处理树形视图双击事件"""
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            if values and len(values) >= 3:
                book_id = values[0]
                book_title = values[1]
                self.book_id_var.set(book_id)
                self.log(f"📋 双击选择书籍: {book_title} (ID: {book_id})", "INFO")
                # 自动开始下载
                self.download_book()

    def download_book(self):
        """下载书籍"""
        book_id = self.book_id_var.get().strip()
        if not book_id:
            messagebox.showwarning("⚠️ 警告", "请输入书籍ID或从搜索结果中选择书籍")
            return

        # 检查是否正在下载
        if self.is_downloading:
            messagebox.showwarning("⚠️ 警告", "正在下载中，请等待当前下载完成后再开始新的下载")
            self.log("⚠️ 下载被阻止：已有下载任务在进行中", "WARNING")
            return

        # 设置下载状态
        self.is_downloading = True

        self.log(f"📥 准备下载书籍 ID: {book_id}", "INFO")
        self.update_status("准备下载...")
        self.show_progress(True)
        self.update_progress(0, "正在获取书籍信息...")

        threading.Thread(target=self._download_worker, args=(book_id,), daemon=True).start()

    def _download_worker(self, book_id):
        """下载工作线程"""
        try:
            # 从 Treeview 获取书籍名称和作者
            selected_item = self.tree.selection()
            if not selected_item:
                self.log(f"❌ 无法下载，因为没有在表格中选择书籍。", "ERROR")
                messagebox.showerror("❌ 错误", f"无法下载，因为没有在表格中选择书籍。")
                self.is_downloading = False
                self.show_progress(False)
                return
                
            # 确保选择的是有效的书籍条目
            item_values = self.tree.item(selected_item, "values")
            if not item_values or len(item_values) < 3:
                self.log(f"❌ 无法下载，选择的书籍信息不完整。", "ERROR")
                messagebox.showerror("❌ 错误", f"无法下载，选择的书籍信息不完整。")
                self.is_downloading = False
                self.show_progress(False)
                return

            item_values = self.tree.item(selected_item, "values")
            if len(item_values) >= 3:
                book_name = item_values[1]
                author = item_values[2]
            else:
                book_name = f"book_{book_id}"
                author = "未知作者"
            
            self.log(f"📚 书名: {book_name}", "SUCCESS")
            self.log(f"✍️ 作者: {author}", "INFO")
            self.current_book_var.set(f"正在下载: {book_name} - {author}")

            # 获取书籍信息
            self.log("📖 正在获取书籍信息...", "INFO")
            self.update_progress(5, "正在获取书籍信息...")

            book_info = self.api.get_book_info(book_id)

            if not (book_info and 'data' in book_info):
                self.log(f"❌ 无法获取书籍信息 (ID: {book_id})", "ERROR")
                self.update_status("获取书籍信息失败")
                messagebox.showerror("❌ 错误", f"无法获取书籍信息 (ID: {book_id})")
                self.is_downloading = False
                self.show_progress(False)
                return

            book_data = book_info['data']
            
            # 获取章节列表
            self.update_progress(10, "正在获取章节列表...")

            item_list = []
            # 检查不同可能的章节列表字段
            if 'chapterListWithVolume' in book_data:
                raw_list = book_data['chapterListWithVolume']
                if isinstance(raw_list, list):
                    # 扁平化嵌套列表
                    if raw_list and isinstance(raw_list[0], list):
                        item_list = raw_list[0]
                    # 兼容带volume字典
                    elif raw_list and isinstance(raw_list[0], dict) and 'chapters' in raw_list[0]:
                        item_list = raw_list[0]['chapters']
                    else:
                        item_list = raw_list
                self.log(f"🔍 从 chapterListWithVolume 找到 {len(item_list)} 个章节", "INFO")
            elif 'item_list' in book_data:
                item_list = book_data['item_list']
                self.log(f"🔍 从 item_list 找到 {len(item_list)} 个章节", "INFO")
            elif 'chapters' in book_data:
                item_list = book_data['chapters']
                self.log(f"🔍 从 chapters 找到 {len(item_list)} 个章节", "INFO")
            
            # 打印章节列表结构以便调试
            if item_list and len(item_list) > 0:
                self.log(f"🔍 章节列表第一项结构: {str(item_list[0])[:30]}...", "INFO")
            
            if not item_list:
                self.log("❌ 未找到章节列表", "ERROR")
                self.update_status("获取章节列表失败")
                messagebox.showerror("❌ 错误", "未找到章节列表")
                self.is_downloading = False
                self.show_progress(False)
                return

            # 提取章节ID，兼容不同的字段名
            item_ids = []
            for item in item_list:
                if 'itemId' in item:
                    item_ids.append(item['itemId'])
                elif 'item_id' in item:
                    item_ids.append(item['item_id'])
                elif 'id' in item:
                    item_ids.append(item['id'])
            
            total_chapters = len(item_ids)
            if total_chapters == 0:
                self.log("❌ 无法提取章节ID", "ERROR")
                self.update_status("获取章节ID失败")
                messagebox.showerror("❌ 错误", "无法提取章节ID")
                self.is_downloading = False
                self.show_progress(False)
                return
                
            self.log(f"📄 共找到 {total_chapters} 个章节", "INFO")

            # 保存原始章节目录用于验证
            original_catalog = []
            for i, item in enumerate(item_list):
                chapter_id = None
                if 'itemId' in item:
                    chapter_id = item['itemId']
                elif 'item_id' in item:
                    chapter_id = item['item_id']
                elif 'id' in item:
                    chapter_id = item['id']

                if chapter_id:
                    original_catalog.append({
                        'index': i,
                        'id': str(chapter_id),
                        'title': item.get('title', f'第{i+1}章')
                    })

            # 分批下载章节（API限制：单次最大30章）
            full_content = f"# {book_name}\n\n**作者**: {author}\n**下载时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
            item_id_chunks = [item_ids[i:i + 30] for i in range(0, len(item_ids), 30)]

            downloaded_chapters = []  # 记录成功下载的章节
            failed_batches = []  # 记录失败的批次

            for i, chunk in enumerate(item_id_chunks):
                progress = 20 + (i / len(item_id_chunks)) * 60  # 20-80%
                self.update_progress(progress, f"下载进度: {i+1}/{len(item_id_chunks)} 批次")

                self.log(f"⬇️ 正在下载第 {i+1}/{len(item_id_chunks)} 批章节...", "INFO")
                item_ids_str = ",".join(map(str, chunk))

                try:
                    content_data = self.api.get_content(item_ids=item_ids_str, api_type='batch')
                    if content_data and 'data' in content_data:
                        if isinstance(content_data['data'], list):
                            batch_success = 0
                            for chapter_content in content_data['data']:
                                chapter_title = chapter_content.get('title', f'第{len(full_content.split("##"))}章')
                                chapter_text = chapter_content.get('content', '')
                                full_content += f"\n\n## {chapter_title}\n\n{chapter_text}"
                                downloaded_chapters.append({
                                    'title': chapter_title,
                                    'id': chapter_content.get('id', ''),
                                    'batch': i + 1
                                })
                                batch_success += 1
                            self.log(f"✅ 第 {i+1} 批下载成功: {batch_success} 章", "SUCCESS")
                        else:
                            self.log(f"⚠️ 第 {i+1} 批章节数据格式不正确: {str(content_data['data'])[:100]}...", "WARNING")
                            failed_batches.append({'batch': i + 1, 'chunk': chunk, 'reason': '数据格式错误'})
                    else:
                        error_msg = str(content_data) if content_data else "无响应数据"
                        self.log(f"⚠️ 第 {i+1} 批章节下载失败: {error_msg[:100]}...", "WARNING")
                        failed_batches.append({'batch': i + 1, 'chunk': chunk, 'reason': error_msg[:100]})
                except Exception as e:
                    self.log(f"❌ 第 {i+1} 批章节下载出错: {str(e)}", "ERROR")
                    failed_batches.append({'batch': i + 1, 'chunk': chunk, 'reason': str(e)})

            # 报告下载统计
            self.log(f"📊 下载统计: 成功 {len(downloaded_chapters)} 章，失败 {len(failed_batches)} 批次", "INFO")

            # 验证章节完整性
            self.update_progress(82, "正在验证章节完整性...")
            self.log("🔍 正在验证章节完整性...", "INFO")

            # 找出缺失的章节
            downloaded_titles = [ch['title'] for ch in downloaded_chapters]
            missing_chapters = []

            for original_ch in original_catalog:
                found = False
                for downloaded_title in downloaded_titles:
                    if (original_ch['title'] in downloaded_title or
                        downloaded_title in original_ch['title'] or
                        self._extract_chapter_number(original_ch['title']) == self._extract_chapter_number(downloaded_title)):
                        found = True
                        break
                if not found:
                    missing_chapters.append(original_ch)

            # 批量重新下载缺失章节
            if missing_chapters:
                self.log(f"⚠️ 发现 {len(missing_chapters)} 个缺失章节，正在批量重新下载...", "WARNING")
                self.update_progress(85, f"正在补充 {len(missing_chapters)} 个缺失章节...")

                # 将缺失章节分批处理（每批30个）
                missing_id_chunks = [missing_chapters[i:i + 30] for i in range(0, len(missing_chapters), 30)]
                retry_success = 0

                for i, chunk in enumerate(missing_id_chunks):
                    try:
                        chunk_ids = [ch['id'] for ch in chunk]
                        chunk_titles = [ch['title'] for ch in chunk]

                        self.log(f"🔄 重新下载第 {i+1}/{len(missing_id_chunks)} 批缺失章节: {len(chunk)} 章", "INFO")

                        content_data = self.api.get_content(item_ids=",".join(chunk_ids), api_type='batch')

                        if content_data and 'data' in content_data and isinstance(content_data['data'], list):
                            for chapter_content in content_data['data']:
                                chapter_title = chapter_content.get('title', '未知章节')
                                chapter_text = chapter_content.get('content', '')
                                full_content += f"\n\n## {chapter_title}\n\n{chapter_text}"
                                retry_success += 1

                            self.log(f"✅ 第 {i+1} 批补充成功: {len(content_data['data'])} 章", "SUCCESS")
                        else:
                            self.log(f"❌ 第 {i+1} 批补充失败: 无有效数据", "ERROR")

                    except Exception as e:
                        self.log(f"❌ 第 {i+1} 批补充出错: {str(e)}", "ERROR")

                self.log(f"📊 缺失章节补充完成: 成功 {retry_success}/{len(missing_chapters)} 章", "INFO")
            else:
                self.log("✅ 章节完整性验证通过", "SUCCESS")

            # 保存文件
            self.update_progress(90, "正在保存文件...")
            self.log("💾 正在保存文件...", "INFO")

            # 清理文件名中的非法字符
            safe_filename = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            file_name = f"{safe_filename}.txt"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(full_content)



            # 最终章节排序
            self.update_progress(95, "正在修复章节顺序...")
            self.log("🔄 正在按目录顺序排列章节...", "INFO")

            try:
                from pathlib import Path
                from fix_chapter_order import reorder_file

                file_path = Path(file_name)
                if reorder_file(file_path, verbose=False):
                    self.log("✅ 章节顺序修复完成", "SUCCESS")
                else:
                    self.log("⚠️ 章节顺序无需修复或修复失败", "WARNING")
            except Exception as e:
                self.log(f"⚠️ 章节顺序修复失败: {str(e)}", "WARNING")

            self.update_progress(100, "下载完成!")
            self.log(f"✅ 下载完成！文件已保存: {file_name}", "SUCCESS")
            self.update_status("下载完成")
            self.current_book_var.set(f"下载完成: {book_name}")

            messagebox.showinfo("🎉 下载成功", f"《{book_name}》下载完成！\n文件保存为: {file_name}\n章节顺序已自动修复")

        except Exception as e:
            self.log(f"❌ 下载出错: {str(e)}", "ERROR")
            self.update_status("下载失败")
            self.current_book_var.set("下载失败")
            messagebox.showerror("❌ 下载失败", f"下载过程中发生错误:\n{str(e)}")
        finally:
            # 重置下载状态
            self.is_downloading = False
            self.show_progress(False)

    def _extract_chapter_number(self, title):
        """从标题中提取章节号"""
        if not title:
            return None

        patterns = [
            r'第(\d+)章',
            r'第(\d+)节',
            r'Chapter\s*(\d+)',
            r'(\d+)\.',
            r'(\d+)\s*[-_]',
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def check_updates_on_startup(self):
        """启动时检查更新"""
        try:
            import time
            time.sleep(2)  # 等待界面完全加载

            from updater import check_and_update
            # GitHub仓库地址
            check_and_update(self, repo_url="POf-L/Fanqie-novel-Downloader")
        except Exception as e:
            print(f"检查更新失败: {str(e)}")

    def manual_check_update(self):
        """手动检查更新"""
        try:
            from updater import check_and_update
            check_and_update(self, repo_url="POf-L/Fanqie-novel-Downloader")
        except Exception as e:
            messagebox.showerror("检查更新失败", f"无法检查更新:\n{str(e)}")


if __name__ == "__main__":
    app = BeautifulApp()
    app.mainloop()
