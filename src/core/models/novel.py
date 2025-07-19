"""
小说数据模型

定义小说的数据结构和相关操作
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Novel:
    """小说数据模型"""
    
    # 基本信息
    book_id: str
    title: str
    author: str
    description: str = ""
    
    # 状态信息
    creation_status: str = "1"  # "0"=完结, "1"=连载中
    read_count: int = 0
    
    # 分类信息
    category_tags: List[Dict[str, Any]] = field(default_factory=list)
    
    # 封面和图片
    thumb_url: str = ""
    
    # 章节信息
    chapters: List['Chapter'] = field(default_factory=list)
    total_chapters: int = 0
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 下载相关
    save_path: str = ""
    download_status: str = "pending"  # pending, downloading, completed, failed
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def is_completed(self) -> bool:
        """是否已完结"""
        return self.creation_status == "0"
    
    @property
    def status_text(self) -> str:
        """状态文本"""
        return "完结" if self.is_completed else "连载中"
    
    @property
    def category_names(self) -> List[str]:
        """分类名称列表"""
        categories = []
        for tag in self.category_tags:
            if isinstance(tag, dict) and tag.get('category_name'):
                categories.append(tag['category_name'])
            elif isinstance(tag, str):
                categories.append(tag)
        return categories
    
    @property
    def category_text(self) -> str:
        """分类文本"""
        categories = self.category_names
        return ' | '.join(categories) if categories else "未分类"
    
    def add_chapter(self, chapter: 'Chapter'):
        """添加章节"""
        self.chapters.append(chapter)
        self.total_chapters = len(self.chapters)
        self.updated_at = datetime.now()
    
    def get_chapter_by_id(self, chapter_id: str) -> Optional['Chapter']:
        """根据ID获取章节"""
        for chapter in self.chapters:
            if chapter.chapter_id == chapter_id:
                return chapter
        return None
    
    def get_chapter_by_index(self, index: int) -> Optional['Chapter']:
        """根据索引获取章节"""
        if 0 <= index < len(self.chapters):
            return self.chapters[index]
        return None
    
    def get_downloaded_chapters(self) -> List['Chapter']:
        """获取已下载的章节"""
        return [ch for ch in self.chapters if ch.is_downloaded]
    
    def get_failed_chapters(self) -> List['Chapter']:
        """获取下载失败的章节"""
        return [ch for ch in self.chapters if ch.download_status == "failed"]
    
    @property
    def download_progress(self) -> float:
        """下载进度（0-100）"""
        if not self.chapters:
            return 0.0
        
        downloaded_count = len(self.get_downloaded_chapters())
        return (downloaded_count / len(self.chapters)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'book_id': self.book_id,
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'creation_status': self.creation_status,
            'read_count': self.read_count,
            'category_tags': self.category_tags,
            'thumb_url': self.thumb_url,
            'total_chapters': self.total_chapters,
            'save_path': self.save_path,
            'download_status': self.download_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'chapters': [ch.to_dict() for ch in self.chapters]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Novel':
        """从字典创建实例"""
        # 处理时间字段
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        # 创建小说实例
        novel = cls(
            book_id=data['book_id'],
            title=data['title'],
            author=data['author'],
            description=data.get('description', ''),
            creation_status=data.get('creation_status', '1'),
            read_count=data.get('read_count', 0),
            category_tags=data.get('category_tags', []),
            thumb_url=data.get('thumb_url', ''),
            total_chapters=data.get('total_chapters', 0),
            save_path=data.get('save_path', ''),
            download_status=data.get('download_status', 'pending'),
            created_at=created_at,
            updated_at=updated_at
        )
        
        # 添加章节
        try:
            from .chapter import Chapter
        except ImportError:
            from chapter import Chapter
        for ch_data in data.get('chapters', []):
            chapter = Chapter.from_dict(ch_data)
            novel.chapters.append(chapter)
        
        return novel
    
    def update_status(self, status: str):
        """更新下载状态"""
        self.download_status = status
        self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        return f"Novel(id={self.book_id}, title='{self.title}', author='{self.author}', chapters={len(self.chapters)})"
    
    def __repr__(self) -> str:
        return self.__str__()


# 便捷函数
def create_novel_from_api_response(api_data: Dict[str, Any]) -> Novel:
    """从API响应创建小说实例"""
    return Novel(
        book_id=str(api_data.get('book_id', '')),
        title=api_data.get('book_name', '未知书名'),
        author=api_data.get('author', '未知作者'),
        description=api_data.get('description', ''),
        creation_status=str(api_data.get('creation_status', '1')),
        read_count=int(api_data.get('read_count', 0)),
        category_tags=api_data.get('category_tags', []),
        thumb_url=api_data.get('thumb_url', '')
    )


__all__ = ["Novel", "create_novel_from_api_response"]
