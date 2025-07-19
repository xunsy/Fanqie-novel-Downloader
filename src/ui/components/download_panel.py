"""
下载面板组件

负责下载相关的UI界面
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable, Optional, Dict, Any

try:
    from ...core.models.novel import Novel
except ImportError:
    try:
        from core.models.novel import Novel
    except ImportError:
        # 创建占位符类
        class Novel:
            def __init__(self):
                self.title = "Unknown"


class DownloadPanel(ctk.CTkFrame):
    """下载面板组件"""
    
    def __init__(self, parent, download_callback: Callable = None, stop_callback: Callable = None):
        """
        初始化下载面板
        
        Args:
            parent: 父组件
            download_callback: 下载回调函数
            stop_callback: 停止回调函数
        """
        super().__init__(parent)
        
        self.download_callback = download_callback
        self.stop_callback = stop_callback
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_widgets()
        self._is_downloading = False
    
    def _create_widgets(self):
        """创建界面组件"""
        # 输入区域
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # 小说ID输入
        ctk.CTkLabel(input_frame, text="小说ID:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.book_id_entry = ctk.CTkEntry(input_frame, placeholder_text="请输入小说ID")
        self.book_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # 保存路径
        ctk.CTkLabel(input_frame, text="保存路径:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.save_path_entry = ctk.CTkEntry(input_frame, placeholder_text="选择保存路径")
        self.save_path_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        self.browse_button = ctk.CTkButton(input_frame, text="浏览", command=self._browse_save_path, width=80)
        self.browse_button.grid(row=1, column=2, padx=10, pady=10)
        
        # 配置网格权重
        input_frame.grid_columnconfigure(1, weight=1)
        
        # 选项区域
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="下载选项:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 输出格式选项
        format_frame = ctk.CTkFrame(options_frame)
        format_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(format_frame, text="输出格式:").pack(side="left", padx=10, pady=10)
        
        self.format_var = ctk.StringVar(value="TXT")
        self.format_radio_txt = ctk.CTkRadioButton(format_frame, text="TXT", variable=self.format_var, value="TXT")
        self.format_radio_txt.pack(side="left", padx=10, pady=10)
        
        self.format_radio_epub = ctk.CTkRadioButton(format_frame, text="EPUB", variable=self.format_var, value="EPUB")
        self.format_radio_epub.pack(side="left", padx=10, pady=10)
        
        self.format_radio_both = ctk.CTkRadioButton(format_frame, text="TXT+EPUB", variable=self.format_var, value="BOTH")
        self.format_radio_both.pack(side="left", padx=10, pady=10)
        
        # 其他选项
        self.enhanced_epub_var = ctk.BooleanVar(value=False)
        self.enhanced_epub_check = ctk.CTkCheckBox(options_frame, text="生成增强版EPUB（包含书籍信息）", variable=self.enhanced_epub_var)
        self.enhanced_epub_check.pack(anchor="w", padx=10, pady=5)
        
        # 控制按钮区域
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.download_button = ctk.CTkButton(
            button_frame, 
            text="开始下载", 
            command=self._start_download,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.download_button.pack(side="left", padx=10, pady=10)
        
        self.stop_button = ctk.CTkButton(
            button_frame, 
            text="停止下载", 
            command=self._stop_download,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=10, pady=10)
        
        # 进度区域
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(progress_frame, text="下载进度:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="等待开始...")
        self.progress_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # 状态区域
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(status_frame, text="当前状态:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.status_text = ctk.CTkTextbox(status_frame, height=100)
        self.status_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.status_text.insert("1.0", "准备就绪，等待开始下载...")
    
    def _browse_save_path(self):
        """浏览保存路径"""
        folder_path = filedialog.askdirectory(title="选择保存目录")
        if folder_path:
            self.save_path_entry.delete(0, "end")
            self.save_path_entry.insert(0, folder_path)
    
    def _start_download(self):
        """开始下载"""
        book_id = self.book_id_entry.get().strip()
        save_path = self.save_path_entry.get().strip()
        
        # 验证输入
        if not book_id:
            messagebox.showerror("错误", "请输入小说ID")
            return
        
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        # 准备下载选项
        options = {
            'format': self.format_var.get(),
            'generate_epub': self.format_var.get() in ["EPUB", "BOTH"],
            'enhanced_epub': self.enhanced_epub_var.get()
        }
        
        # 调用下载回调
        if self.download_callback:
            self.download_callback(book_id, save_path, options)
        
        # 更新UI状态
        self._set_downloading_state(True)
    
    def _stop_download(self):
        """停止下载"""
        if self.stop_callback:
            self.stop_callback()
        
        self._set_downloading_state(False)
    
    def _set_downloading_state(self, is_downloading: bool):
        """设置下载状态"""
        self._is_downloading = is_downloading
        
        if is_downloading:
            self.download_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.book_id_entry.configure(state="disabled")
            self.save_path_entry.configure(state="disabled")
            self.browse_button.configure(state="disabled")
        else:
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.book_id_entry.configure(state="normal")
            self.save_path_entry.configure(state="normal")
            self.browse_button.configure(state="normal")
    
    def update_progress(self, progress: float, current: int, total: int, message: str = ""):
        """更新进度"""
        self.progress_bar.set(progress / 100)
        
        if message:
            self.progress_label.configure(text=message)
        else:
            self.progress_label.configure(text=f"进度: {current}/{total} ({progress:.1f}%)")
    
    def update_status(self, message: str):
        """更新状态"""
        self.status_text.insert("end", f"\n{message}")
        self.status_text.see("end")
    
    def on_download_start(self, novel: Novel):
        """下载开始回调"""
        self.update_status(f"开始下载: {novel.title}")
        self.progress_bar.set(0)
        self.progress_label.configure(text="正在获取章节列表...")
    
    def on_download_complete(self, novel: Novel):
        """下载完成回调"""
        self.update_status(f"下载完成: {novel.title}")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="下载完成！")
        self._set_downloading_state(False)
    
    def on_download_error(self, error: str):
        """下载错误回调"""
        self.update_status(f"下载出错: {error}")
        self._set_downloading_state(False)
    
    def refresh(self):
        """刷新面板"""
        if not self._is_downloading:
            self.progress_bar.set(0)
            self.progress_label.configure(text="等待开始...")


__all__ = ["DownloadPanel"]
