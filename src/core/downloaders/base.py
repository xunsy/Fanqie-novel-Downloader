"""
下载器基类

定义下载器的基础接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any, List
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..models.novel import Novel
    from ..models.chapter import Chapter
except ImportError:
    try:
        from core.models.novel import Novel
        from core.models.chapter import Chapter
    except ImportError:
        # 如果导入失败，创建占位符类
        class Novel:
            pass
        class Chapter:
            pass


class DownloadCallback:
    """下载回调接口"""
    
    def on_start(self, novel: Novel):
        """下载开始"""
        pass
    
    def on_progress(self, novel: Novel, current: int, total: int, message: str = ""):
        """下载进度更新"""
        pass
    
    def on_chapter_start(self, chapter: Chapter):
        """章节下载开始"""
        pass
    
    def on_chapter_complete(self, chapter: Chapter):
        """章节下载完成"""
        pass
    
    def on_chapter_failed(self, chapter: Chapter, error: str):
        """章节下载失败"""
        pass
    
    def on_complete(self, novel: Novel):
        """下载完成"""
        pass
    
    def on_error(self, novel: Novel, error: str):
        """下载出错"""
        pass


class BaseDownloader(ABC):
    """下载器基类"""
    
    def __init__(self, max_workers: int = 4, request_timeout: int = 15, 
                 max_retries: int = 3, rate_limit: float = 0.5):
        """
        初始化下载器
        
        Args:
            max_workers: 最大并发数
            request_timeout: 请求超时时间
            max_retries: 最大重试次数
            rate_limit: 请求间隔（秒）
        """
        self.max_workers = max_workers
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        
        # 状态控制
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._is_running = False
        
        # 回调
        self.callback: Optional[DownloadCallback] = None
        
        # 统计信息
        self.stats = {
            'total_chapters': 0,
            'completed_chapters': 0,
            'failed_chapters': 0,
            'start_time': None,
            'end_time': None
        }
    
    def set_callback(self, callback: DownloadCallback):
        """设置回调"""
        self.callback = callback
    
    def stop(self):
        """停止下载"""
        self._stop_flag.set()
    
    def pause(self):
        """暂停下载"""
        self._pause_flag.set()
    
    def resume(self):
        """恢复下载"""
        self._pause_flag.clear()
    
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self._stop_flag.is_set()
    
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._pause_flag.is_set()
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    def wait_if_paused(self):
        """如果暂停则等待"""
        while self._pause_flag.is_set() and not self._stop_flag.is_set():
            time.sleep(0.1)
    
    def check_stop_flag(self):
        """检查停止标志"""
        if self._stop_flag.is_set():
            raise InterruptedError("下载已停止")
    
    @abstractmethod
    def get_novel_info(self, book_id: str) -> Novel:
        """
        获取小说信息
        
        Args:
            book_id: 小说ID
            
        Returns:
            Novel: 小说对象
        """
        pass
    
    @abstractmethod
    def get_chapter_list(self, novel: Novel) -> List[Chapter]:
        """
        获取章节列表
        
        Args:
            novel: 小说对象
            
        Returns:
            List[Chapter]: 章节列表
        """
        pass
    
    @abstractmethod
    def download_chapter_content(self, chapter: Chapter) -> str:
        """
        下载章节内容
        
        Args:
            chapter: 章节对象
            
        Returns:
            str: 章节内容
        """
        pass
    
    def download_novel(self, book_id: str) -> Novel:
        """
        下载小说
        
        Args:
            book_id: 小说ID
            
        Returns:
            Novel: 下载完成的小说对象
        """
        try:
            self._is_running = True
            self._stop_flag.clear()
            self._pause_flag.clear()
            
            # 重置统计信息
            self.stats['start_time'] = time.time()
            self.stats['completed_chapters'] = 0
            self.stats['failed_chapters'] = 0
            
            # 获取小说信息
            novel = self.get_novel_info(book_id)
            novel.update_status("downloading")
            
            if self.callback:
                self.callback.on_start(novel)
            
            # 获取章节列表
            chapters = self.get_chapter_list(novel)
            novel.chapters = chapters
            novel.total_chapters = len(chapters)
            
            self.stats['total_chapters'] = len(chapters)
            
            # 下载章节
            self._download_chapters(novel)
            
            # 更新状态
            if novel.get_failed_chapters():
                novel.update_status("partial")
            else:
                novel.update_status("completed")
            
            self.stats['end_time'] = time.time()
            
            if self.callback:
                self.callback.on_complete(novel)
            
            return novel
            
        except Exception as e:
            if self.callback:
                self.callback.on_error(novel if 'novel' in locals() else None, str(e))
            raise
        finally:
            self._is_running = False
    
    def _download_chapters(self, novel: Novel):
        """下载章节（并发）"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交下载任务
            future_to_chapter = {}
            for chapter in novel.chapters:
                if not chapter.is_downloaded:
                    future = executor.submit(self._download_single_chapter, chapter)
                    future_to_chapter[future] = chapter
            
            # 处理完成的任务
            for future in as_completed(future_to_chapter):
                self.check_stop_flag()
                self.wait_if_paused()
                
                chapter = future_to_chapter[future]
                try:
                    success = future.result()
                    if success:
                        self.stats['completed_chapters'] += 1
                        if self.callback:
                            self.callback.on_chapter_complete(chapter)
                    else:
                        self.stats['failed_chapters'] += 1
                        if self.callback:
                            self.callback.on_chapter_failed(chapter, chapter.error_message)
                    
                    # 更新进度
                    if self.callback:
                        completed = self.stats['completed_chapters']
                        total = self.stats['total_chapters']
                        self.callback.on_progress(novel, completed, total, f"已完成 {completed}/{total} 章节")
                        
                except Exception as e:
                    chapter.fail_download(str(e))
                    self.stats['failed_chapters'] += 1
                    if self.callback:
                        self.callback.on_chapter_failed(chapter, str(e))
    
    def _download_single_chapter(self, chapter: Chapter) -> bool:
        """下载单个章节"""
        for attempt in range(self.max_retries):
            try:
                self.check_stop_flag()
                self.wait_if_paused()
                
                chapter.start_download()
                if self.callback:
                    self.callback.on_chapter_start(chapter)
                
                # 下载内容
                content = self.download_chapter_content(chapter)
                
                if content and content.strip():
                    chapter.complete_download(content)
                    return True
                else:
                    raise ValueError("章节内容为空")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit * (attempt + 1))  # 指数退避
                else:
                    chapter.fail_download(str(e))
                    return False
        
        return False
    
    def get_download_stats(self) -> Dict[str, Any]:
        """获取下载统计信息"""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration'] = stats['end_time'] - stats['start_time']
        elif stats['start_time']:
            stats['duration'] = time.time() - stats['start_time']
        else:
            stats['duration'] = 0
        
        return stats


__all__ = ["BaseDownloader", "DownloadCallback"]
