"""
章节数据模型

定义章节的数据结构和相关操作
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Chapter:
    """章节数据模型"""
    
    # 基本信息
    chapter_id: str
    title: str
    content: str = ""
    
    # 位置信息
    index: int = 0  # 章节在小说中的索引
    
    # 下载状态
    download_status: str = "pending"  # pending, downloading, completed, failed
    download_attempts: int = 0
    max_retries: int = 3
    
    # 错误信息
    error_message: str = ""
    
    # 时间信息
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    
    # 元数据
    word_count: int = 0
    is_vip: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        # 计算字数
        if self.content:
            self.word_count = len(self.content.strip())
    
    @property
    def is_downloaded(self) -> bool:
        """是否已下载"""
        return self.download_status == "completed" and bool(self.content.strip())
    
    @property
    def is_failed(self) -> bool:
        """是否下载失败"""
        return self.download_status == "failed"
    
    @property
    def is_pending(self) -> bool:
        """是否等待下载"""
        return self.download_status == "pending"
    
    @property
    def is_downloading(self) -> bool:
        """是否正在下载"""
        return self.download_status == "downloading"
    
    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.download_attempts < self.max_retries
    
    @property
    def status_text(self) -> str:
        """状态文本"""
        status_map = {
            "pending": "等待下载",
            "downloading": "下载中",
            "completed": "已完成",
            "failed": "下载失败"
        }
        return status_map.get(self.download_status, "未知状态")
    
    def start_download(self):
        """开始下载"""
        self.download_status = "downloading"
        self.download_attempts += 1
        self.updated_at = datetime.now()
        self.error_message = ""
    
    def complete_download(self, content: str):
        """完成下载"""
        self.content = content
        self.download_status = "completed"
        self.downloaded_at = datetime.now()
        self.updated_at = datetime.now()
        self.word_count = len(content.strip())
        self.error_message = ""
    
    def fail_download(self, error_message: str = ""):
        """下载失败"""
        self.download_status = "failed"
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def reset_download(self):
        """重置下载状态"""
        self.download_status = "pending"
        self.download_attempts = 0
        self.error_message = ""
        self.content = ""
        self.word_count = 0
        self.downloaded_at = None
        self.updated_at = datetime.now()
    
    def update_content(self, content: str):
        """更新内容"""
        self.content = content
        self.word_count = len(content.strip())
        self.updated_at = datetime.now()
        
        # 如果有内容且状态不是已完成，则标记为已完成
        if content.strip() and self.download_status != "completed":
            self.download_status = "completed"
            self.downloaded_at = datetime.now()
    
    def get_clean_title(self) -> str:
        """获取清理后的标题"""
        import re
        # 移除特殊字符，保留中文、英文、数字和常见标点
        clean_title = re.sub(r'[^\w\s\u4e00-\u9fff\-_()（）【】]', '', self.title)
        return clean_title.strip()
    
    def get_filename_safe_title(self) -> str:
        """获取文件名安全的标题"""
        try:
            from ...utils.file_utils import sanitize_filename
        except ImportError:
            try:
                from utils.file_utils import sanitize_filename
            except ImportError:
                # 如果导入失败，使用简单的清理方法
                import re
                title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', self.title)
                return title.strip(' .')
        return sanitize_filename(self.title)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chapter_id': self.chapter_id,
            'title': self.title,
            'content': self.content,
            'index': self.index,
            'download_status': self.download_status,
            'download_attempts': self.download_attempts,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'word_count': self.word_count,
            'is_vip': self.is_vip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chapter':
        """从字典创建实例"""
        # 处理时间字段
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        downloaded_at = None
        if data.get('downloaded_at'):
            downloaded_at = datetime.fromisoformat(data['downloaded_at'])
        
        return cls(
            chapter_id=data['chapter_id'],
            title=data['title'],
            content=data.get('content', ''),
            index=data.get('index', 0),
            download_status=data.get('download_status', 'pending'),
            download_attempts=data.get('download_attempts', 0),
            max_retries=data.get('max_retries', 3),
            error_message=data.get('error_message', ''),
            word_count=data.get('word_count', 0),
            is_vip=data.get('is_vip', False),
            created_at=created_at,
            updated_at=updated_at,
            downloaded_at=downloaded_at
        )
    
    def __str__(self) -> str:
        return f"Chapter(id={self.chapter_id}, title='{self.title}', status={self.download_status})"
    
    def __repr__(self) -> str:
        return self.__str__()


# 便捷函数
def create_chapter_from_api_response(api_data: Dict[str, Any], index: int = 0) -> Chapter:
    """从API响应创建章节实例"""
    return Chapter(
        chapter_id=str(api_data.get('chapter_id', '')),
        title=api_data.get('title', f'第{index+1}章'),
        index=index,
        is_vip=api_data.get('is_vip', False)
    )


def create_chapters_from_list(chapters_data: list) -> list:
    """从章节列表创建章节实例列表"""
    chapters = []
    for i, ch_data in enumerate(chapters_data):
        chapter = create_chapter_from_api_response(ch_data, i)
        chapters.append(chapter)
    return chapters


__all__ = ["Chapter", "create_chapter_from_api_response", "create_chapters_from_list"]
