"""
主窗口模块

重构后的主窗口，分离了界面和业务逻辑
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict, Any
import threading

try:
    from .components.download_panel import DownloadPanel
    from .components.settings_panel import SettingsPanel
    from .components.log_panel import LogPanel
    from ..core.downloaders.novel_downloader import NovelDownloader
    from ..core.downloaders.base import DownloadCallback
    from ..core.models.novel import Novel
    from ..core.models.chapter import Chapter
    from ..config.settings import get_config, save_config
    from ..services.logging_service import get_logger
    from ..services.update_service import check_update
    from ..utils.ui_utils import center_window_on_screen
except ImportError:
    try:
        from ui.components.download_panel import DownloadPanel
        from ui.components.settings_panel import SettingsPanel
        from ui.components.log_panel import LogPanel
        from core.downloaders.novel_downloader import NovelDownloader
        from core.downloaders.base import DownloadCallback
        from core.models.novel import Novel
        from core.models.chapter import Chapter
        from config.settings import get_config, save_config
        from services.logging_service import get_logger
        from services.update_service import check_update
        from utils.ui_utils import center_window_on_screen
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有模块都在正确的位置")
        raise


class NovelDownloaderGUI(ctk.CTk, DownloadCallback):
    """重构后的主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化日志
        self.logger = get_logger("gui")
        self.logger.info("初始化主窗口")
        
        # 加载配置
        self.config = get_config()
        
        # 初始化变量
        self.current_downloader: Optional[NovelDownloader] = None
        self.download_thread: Optional[threading.Thread] = None
        
        # 设置窗口
        self._setup_window()
        
        # 创建界面
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
        # 检查更新
        self._check_for_updates()
    
    def _setup_window(self):
        """设置窗口属性"""
        # 设置主题
        ctk.set_appearance_mode(self.config.get('ui.appearance_mode', 'dark'))
        ctk.set_default_color_theme(self.config.get('ui.color_theme', 'blue'))
        
        # 设置窗口标题和大小
        self.title("番茄小说下载器 v2.0 - 模块化版本")
        
        # 获取窗口配置
        window_config = self.config.get('window', {})
        geometry = window_config.get('default_geometry', '1300x850')
        self.geometry(geometry)
        
        # 设置最小尺寸
        min_width = window_config.get('min_width', 800)
        min_height = window_config.get('min_height', 600)
        self.minsize(min_width, min_height)
        
        # 居中显示
        center_window_on_screen(self)
        
        # 设置关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 下载标签页
        self.download_tab = self.tabview.add("下载")
        self.download_panel = DownloadPanel(
            self.download_tab, 
            download_callback=self._start_download,
            stop_callback=self._stop_download
        )
        
        # 设置标签页
        self.settings_tab = self.tabview.add("设置")
        self.settings_panel = SettingsPanel(
            self.settings_tab,
            config_changed_callback=self._on_config_changed
        )
        
        # 日志标签页
        self.log_tab = self.tabview.add("日志")
        self.log_panel = LogPanel(self.log_tab)
        
        # 设置默认标签页
        self.tabview.set("下载")
    
    def _bind_events(self):
        """绑定事件"""
        # 窗口大小改变事件
        self.bind("<Configure>", self._on_window_configure)
        
        # 键盘快捷键
        self.bind("<Control-q>", lambda e: self._on_closing())
        self.bind("<F5>", lambda e: self._refresh_ui())
    
    def _check_for_updates(self):
        """检查更新"""
        def check_update_thread():
            try:
                update_message = check_update()
                if update_message:
                    self.after(0, lambda: self._show_update_notification(update_message))
            except Exception as e:
                self.logger.error(f"检查更新失败: {e}")
        
        # 在后台线程中检查更新
        threading.Thread(target=check_update_thread, daemon=True).start()
    
    def _show_update_notification(self, message: str):
        """显示更新通知"""
        from tkinter import messagebox
        messagebox.showinfo("更新提示", message, parent=self)
    
    def _start_download(self, book_id: str, save_path: str, options: Dict[str, Any]):
        """开始下载"""
        if self.download_thread and self.download_thread.is_alive():
            self.log_panel.add_log("下载正在进行中，请等待完成", "warning")
            return
        
        try:
            # 创建下载器
            downloader_config = {
                'max_workers': self.config.get('request.max_workers', 4),
                'request_timeout': self.config.get('request.timeout', 15),
                'max_retries': self.config.get('request.max_retries', 3),
                'rate_limit': self.config.get('request.request_rate_limit', 0.5),
                'api_endpoints': self.config.get('api.endpoints', [])
            }
            
            self.current_downloader = NovelDownloader(downloader_config)
            self.current_downloader.set_callback(self)
            
            # 在新线程中开始下载
            self.download_thread = threading.Thread(
                target=self._download_worker,
                args=(book_id, save_path, options),
                daemon=True
            )
            self.download_thread.start()
            
            self.log_panel.add_log(f"开始下载小说 ID: {book_id}", "info")
            
        except Exception as e:
            self.logger.exception("启动下载失败")
            self.log_panel.add_log(f"启动下载失败: {e}", "error")
    
    def _download_worker(self, book_id: str, save_path: str, options: Dict[str, Any]):
        """下载工作线程"""
        try:
            novel = self.current_downloader.download_novel(book_id)
            
            # 保存文件
            self.after(0, lambda: self._save_downloaded_novel(novel, save_path, options))
            
        except Exception as e:
            self.logger.exception("下载过程中出错")
            self.after(0, lambda: self.log_panel.add_log(f"下载失败: {e}", "error"))
    
    def _save_downloaded_novel(self, novel: Novel, save_path: str, options: Dict[str, Any]):
        """保存下载的小说"""
        try:
            from ..core.storage.file_manager import FileManager
            from ..utils.format_converter import generate_epub, generate_enhanced_epub
            
            file_manager = FileManager(save_path)
            
            # 保存为TXT
            txt_path = file_manager.save_novel_as_txt(novel)
            self.log_panel.add_log(f"TXT文件已保存: {txt_path}", "success")
            
            # 如果需要生成EPUB
            if options.get('generate_epub', False):
                epub_path = txt_path.replace('.txt', '.epub')
                if options.get('enhanced_epub', False):
                    success = generate_enhanced_epub(txt_path, save_path, novel.to_dict())
                else:
                    success = generate_epub(txt_path, save_path, novel.title, novel.author, novel.description)
                
                if success:
                    self.log_panel.add_log(f"EPUB文件已生成: {epub_path}", "success")
                else:
                    self.log_panel.add_log("EPUB文件生成失败", "error")
            
            # 保存元数据
            file_manager.save_novel_metadata(novel)
            file_manager.save_download_status(novel)
            
            self.log_panel.add_log("下载完成！", "success")
            
        except Exception as e:
            self.logger.exception("保存文件失败")
            self.log_panel.add_log(f"保存文件失败: {e}", "error")
    
    def _stop_download(self):
        """停止下载"""
        if self.current_downloader:
            self.current_downloader.stop()
            self.log_panel.add_log("正在停止下载...", "warning")
    
    def _on_config_changed(self, config_key: str, new_value: Any):
        """配置改变回调"""
        self.logger.info(f"配置已更改: {config_key} = {new_value}")
        save_config()
    
    def _refresh_ui(self):
        """刷新界面"""
        self.download_panel.refresh()
        self.settings_panel.refresh()
        self.log_panel.refresh()
    
    def _on_window_configure(self, event):
        """窗口配置改变事件"""
        if event.widget == self:
            # 保存窗口大小和位置
            geometry = self.geometry()
            self.config['window']['default_geometry'] = geometry
    
    def _on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止下载
            if self.current_downloader:
                self.current_downloader.stop()
            
            # 等待下载线程结束
            if self.download_thread and self.download_thread.is_alive():
                self.download_thread.join(timeout=2)
            
            # 保存配置
            save_config()
            
            self.logger.info("应用程序正常退出")
            
        except Exception as e:
            self.logger.exception("退出时出错")
        finally:
            self.destroy()
    
    # DownloadCallback 接口实现
    def on_start(self, novel: Novel):
        """下载开始回调"""
        self.after(0, lambda: self.download_panel.on_download_start(novel))
        self.after(0, lambda: self.log_panel.add_log(f"开始下载: {novel.title}", "info"))
    
    def on_progress(self, novel: Novel, current: int, total: int, message: str = ""):
        """下载进度回调"""
        progress = (current / total * 100) if total > 0 else 0
        self.after(0, lambda: self.download_panel.update_progress(progress, current, total, message))
    
    def on_chapter_start(self, chapter: Chapter):
        """章节开始下载回调"""
        self.after(0, lambda: self.log_panel.add_log(f"开始下载章节: {chapter.title}", "debug"))
    
    def on_chapter_complete(self, chapter: Chapter):
        """章节下载完成回调"""
        self.after(0, lambda: self.log_panel.add_log(f"章节下载完成: {chapter.title}", "debug"))
    
    def on_chapter_failed(self, chapter: Chapter, error: str):
        """章节下载失败回调"""
        self.after(0, lambda: self.log_panel.add_log(f"章节下载失败: {chapter.title} - {error}", "error"))
    
    def on_complete(self, novel: Novel):
        """下载完成回调"""
        self.after(0, lambda: self.download_panel.on_download_complete(novel))
        self.after(0, lambda: self.log_panel.add_log(f"下载完成: {novel.title}", "success"))
    
    def on_error(self, novel: Novel, error: str):
        """下载错误回调"""
        self.after(0, lambda: self.download_panel.on_download_error(error))
        self.after(0, lambda: self.log_panel.add_log(f"下载出错: {error}", "error"))


__all__ = ["NovelDownloaderGUI"]
