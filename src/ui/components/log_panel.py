"""
日志面板组件

负责显示应用日志的UI界面
"""

import customtkinter as ctk
from datetime import datetime
from typing import Literal
import threading


class LogPanel(ctk.CTkFrame):
    """日志面板组件"""
    
    def __init__(self, parent):
        """
        初始化日志面板
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_widgets()
        self._log_lock = threading.Lock()
        
        # 日志级别颜色映射
        self.level_colors = {
            "debug": "#888888",
            "info": "#FFFFFF", 
            "success": "#00FF00",
            "warning": "#FFA500",
            "error": "#FF0000",
            "system": "#00BFFF"
        }
    
    def _create_widgets(self):
        """创建界面组件"""
        # 标题和控制区域
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="应用日志", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
        
        # 控制按钮
        self.clear_button = ctk.CTkButton(
            header_frame, 
            text="清空日志", 
            command=self._clear_logs,
            width=80
        )
        self.clear_button.pack(side="right", padx=10, pady=10)
        
        self.save_button = ctk.CTkButton(
            header_frame, 
            text="保存日志", 
            command=self._save_logs,
            width=80
        )
        self.save_button.pack(side="right", padx=10, pady=10)
        
        # 过滤选项
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(filter_frame, text="日志级别:").pack(side="left", padx=10, pady=10)
        
        self.level_filter_var = ctk.StringVar(value="all")
        self.level_filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.level_filter_var,
            values=["all", "debug", "info", "success", "warning", "error", "system"],
            command=self._on_filter_changed
        )
        self.level_filter_menu.pack(side="left", padx=10, pady=10)
        
        # 自动滚动选项
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_check = ctk.CTkCheckBox(
            filter_frame, 
            text="自动滚动", 
            variable=self.auto_scroll_var
        )
        self.auto_scroll_check.pack(side="right", padx=10, pady=10)
        
        # 日志显示区域
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 状态栏
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(status_frame, text="日志就绪")
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.log_count_label = ctk.CTkLabel(status_frame, text="日志条数: 0")
        self.log_count_label.pack(side="right", padx=10, pady=5)
        
        # 初始化日志计数
        self._log_count = 0
        self._filtered_logs = []
        self._all_logs = []
    
    def add_log(self, message: str, level: Literal["debug", "info", "success", "warning", "error", "system"] = "info"):
        """
        添加日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        with self._log_lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "full_text": f"[{timestamp}] [{level.upper()}] {message}"
            }
            
            self._all_logs.append(log_entry)
            self._log_count += 1
            
            # 检查是否需要显示此日志
            if self._should_show_log(log_entry):
                self._filtered_logs.append(log_entry)
                self._display_log(log_entry)
            
            # 更新状态
            self._update_status()
    
    def _should_show_log(self, log_entry: dict) -> bool:
        """检查是否应该显示此日志"""
        filter_level = self.level_filter_var.get()
        return filter_level == "all" or filter_level == log_entry["level"]
    
    def _display_log(self, log_entry: dict):
        """显示日志条目"""
        # 获取颜色
        color = self.level_colors.get(log_entry["level"], "#FFFFFF")
        
        # 插入日志
        self.log_text.insert("end", log_entry["full_text"] + "\n")
        
        # 设置颜色（如果支持的话）
        try:
            # 获取最后一行的位置
            last_line_start = self.log_text.index("end-2c linestart")
            last_line_end = self.log_text.index("end-2c lineend")
            
            # 创建标签并应用颜色
            tag_name = f"level_{log_entry['level']}"
            self.log_text.tag_add(tag_name, last_line_start, last_line_end)
            self.log_text.tag_config(tag_name, foreground=color)
        except Exception:
            pass  # 如果设置颜色失败，忽略错误
        
        # 自动滚动
        if self.auto_scroll_var.get():
            self.log_text.see("end")
    
    def _on_filter_changed(self, value):
        """过滤器改变事件"""
        self._refresh_display()
    
    def _refresh_display(self):
        """刷新显示"""
        # 清空显示
        self.log_text.delete("1.0", "end")
        self._filtered_logs.clear()
        
        # 重新过滤和显示
        for log_entry in self._all_logs:
            if self._should_show_log(log_entry):
                self._filtered_logs.append(log_entry)
                self._display_log(log_entry)
        
        self._update_status()
    
    def _clear_logs(self):
        """清空日志"""
        with self._log_lock:
            self.log_text.delete("1.0", "end")
            self._all_logs.clear()
            self._filtered_logs.clear()
            self._log_count = 0
            self._update_status()
    
    def _save_logs(self):
        """保存日志"""
        from tkinter import filedialog
        
        if not self._all_logs:
            from tkinter import messagebox
            messagebox.showinfo("提示", "没有日志可保存")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"番茄小说下载器日志\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for log_entry in self._all_logs:
                        f.write(log_entry["full_text"] + "\n")
                
                from tkinter import messagebox
                messagebox.showinfo("成功", f"日志已保存到: {file_path}")
                
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("错误", f"保存日志失败: {e}")
    
    def _update_status(self):
        """更新状态"""
        total_count = len(self._all_logs)
        filtered_count = len(self._filtered_logs)
        
        if self.level_filter_var.get() == "all":
            self.log_count_label.configure(text=f"日志条数: {total_count}")
        else:
            self.log_count_label.configure(text=f"日志条数: {filtered_count}/{total_count}")
        
        # 更新状态文本
        if total_count == 0:
            self.status_label.configure(text="日志就绪")
        else:
            latest_log = self._all_logs[-1]
            self.status_label.configure(text=f"最新: [{latest_log['level'].upper()}] {latest_log['message'][:50]}...")
    
    def refresh(self):
        """刷新面板"""
        self._refresh_display()
    
    def get_log_count(self) -> int:
        """获取日志总数"""
        return len(self._all_logs)
    
    def get_filtered_log_count(self) -> int:
        """获取过滤后的日志数"""
        return len(self._filtered_logs)
    
    def export_logs(self) -> list:
        """导出所有日志"""
        return self._all_logs.copy()


__all__ = ["LogPanel"]
