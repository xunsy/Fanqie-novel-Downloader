"""
文件管理器

负责小说文件的保存、读取和管理
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from ..models.novel import Novel
    from ..models.chapter import Chapter
    from ...utils.file_utils import sanitize_filename, ensure_directory_exists
except ImportError:
    try:
        from core.models.novel import Novel
        from core.models.chapter import Chapter
        from utils.file_utils import sanitize_filename, ensure_directory_exists
    except ImportError:
        # 创建占位符和基础函数
        class Novel:
            pass
        class Chapter:
            pass
        def sanitize_filename(name):
            import re
            return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
        def ensure_directory_exists(path):
            import os
            os.makedirs(path, exist_ok=True)


class FileManager:
    """文件管理器"""
    
    def __init__(self, base_path: str = "downloads"):
        """
        初始化文件管理器
        
        Args:
            base_path: 基础保存路径
        """
        self.base_path = base_path
        ensure_directory_exists(self.base_path)
    
    def get_novel_directory(self, novel: Novel) -> str:
        """获取小说目录路径"""
        safe_title = sanitize_filename(f"{novel.title}_{novel.author}")
        novel_dir = os.path.join(self.base_path, safe_title)
        ensure_directory_exists(novel_dir)
        return novel_dir
    
    def save_novel_as_txt(self, novel: Novel, output_path: Optional[str] = None) -> str:
        """
        保存小说为TXT文件
        
        Args:
            novel: 小说对象
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            str: 保存的文件路径
        """
        if output_path is None:
            novel_dir = self.get_novel_directory(novel)
            safe_title = sanitize_filename(novel.title)
            output_path = os.path.join(novel_dir, f"{safe_title}.txt")
        
        # 确保输出目录存在
        ensure_directory_exists(os.path.dirname(output_path))
        
        # 生成TXT内容
        content_lines = []
        
        # 添加书籍信息
        content_lines.append(f"书名：{novel.title}")
        content_lines.append(f"作者：{novel.author}")
        content_lines.append(f"状态：{novel.status_text}")
        if novel.description:
            content_lines.append(f"简介：{novel.description}")
        content_lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append("=" * 50)
        content_lines.append("")
        
        # 添加章节内容
        for chapter in novel.chapters:
            if chapter.is_downloaded and chapter.content:
                content_lines.append(chapter.title)
                content_lines.append("")
                content_lines.append(chapter.content)
                content_lines.append("")
                content_lines.append("-" * 30)
                content_lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        return output_path
    
    def save_novel_metadata(self, novel: Novel, output_path: Optional[str] = None) -> str:
        """
        保存小说元数据为JSON文件
        
        Args:
            novel: 小说对象
            output_path: 输出路径
            
        Returns:
            str: 保存的文件路径
        """
        if output_path is None:
            novel_dir = self.get_novel_directory(novel)
            output_path = os.path.join(novel_dir, "metadata.json")
        
        # 确保输出目录存在
        ensure_directory_exists(os.path.dirname(output_path))
        
        # 保存元数据
        metadata = novel.to_dict()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def load_novel_metadata(self, metadata_path: str) -> Optional[Novel]:
        """
        从JSON文件加载小说元数据
        
        Args:
            metadata_path: 元数据文件路径
            
        Returns:
            Optional[Novel]: 小说对象，失败返回None
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Novel.from_dict(data)
        except Exception as e:
            print(f"加载小说元数据失败: {e}")
            return None
    
    def save_download_status(self, novel: Novel, status_path: Optional[str] = None) -> str:
        """
        保存下载状态
        
        Args:
            novel: 小说对象
            status_path: 状态文件路径
            
        Returns:
            str: 保存的文件路径
        """
        if status_path is None:
            novel_dir = self.get_novel_directory(novel)
            status_path = os.path.join(novel_dir, "download_status.json")
        
        # 确保输出目录存在
        ensure_directory_exists(os.path.dirname(status_path))
        
        # 生成状态数据
        status_data = {
            'book_id': novel.book_id,
            'title': novel.title,
            'total_chapters': novel.total_chapters,
            'downloaded_chapters': len(novel.get_downloaded_chapters()),
            'failed_chapters': len(novel.get_failed_chapters()),
            'download_progress': novel.download_progress,
            'download_status': novel.download_status,
            'last_updated': datetime.now().isoformat(),
            'chapters': [
                {
                    'chapter_id': ch.chapter_id,
                    'title': ch.title,
                    'index': ch.index,
                    'download_status': ch.download_status,
                    'error_message': ch.error_message,
                    'download_attempts': ch.download_attempts
                }
                for ch in novel.chapters
            ]
        }
        
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        return status_path
    
    def load_download_status(self, status_path: str) -> Optional[Dict[str, Any]]:
        """
        加载下载状态
        
        Args:
            status_path: 状态文件路径
            
        Returns:
            Optional[Dict]: 状态数据，失败返回None
        """
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载下载状态失败: {e}")
            return None
    
    def list_downloaded_novels(self) -> List[Dict[str, Any]]:
        """
        列出已下载的小说
        
        Returns:
            List[Dict]: 小说信息列表
        """
        novels = []
        
        if not os.path.exists(self.base_path):
            return novels
        
        for item in os.listdir(self.base_path):
            item_path = os.path.join(self.base_path, item)
            if os.path.isdir(item_path):
                # 查找元数据文件
                metadata_path = os.path.join(item_path, "metadata.json")
                if os.path.exists(metadata_path):
                    novel = self.load_novel_metadata(metadata_path)
                    if novel:
                        novels.append({
                            'novel': novel,
                            'directory': item_path,
                            'metadata_path': metadata_path
                        })
        
        return novels
    
    def delete_novel_files(self, novel: Novel) -> bool:
        """
        删除小说文件
        
        Args:
            novel: 小说对象
            
        Returns:
            bool: 删除成功返回True
        """
        try:
            novel_dir = self.get_novel_directory(novel)
            if os.path.exists(novel_dir):
                import shutil
                shutil.rmtree(novel_dir)
            return True
        except Exception as e:
            print(f"删除小说文件失败: {e}")
            return False
    
    def get_novel_file_size(self, novel: Novel) -> int:
        """
        获取小说文件总大小
        
        Args:
            novel: 小说对象
            
        Returns:
            int: 文件大小（字节）
        """
        total_size = 0
        novel_dir = self.get_novel_directory(novel)
        
        if os.path.exists(novel_dir):
            for root, dirs, files in os.walk(novel_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        continue
        
        return total_size


__all__ = ["FileManager"]
