"""
小说下载器主类

整合不同的下载策略，提供统一的下载接口
"""

from typing import Optional, Dict, Any, List
import requests
import time

try:
    from .base import BaseDownloader, DownloadCallback
    from ..models.novel import Novel, create_novel_from_api_response
    from ..models.chapter import Chapter, create_chapters_from_list
    from ...utils.network_utils import make_request, create_session_with_retries
except ImportError:
    try:
        from core.downloaders.base import BaseDownloader, DownloadCallback
        from core.models.novel import Novel, create_novel_from_api_response
        from core.models.chapter import Chapter, create_chapters_from_list
        from utils.network_utils import make_request, create_session_with_retries
    except ImportError:
        # 如果还是失败，使用绝对导入
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from core.downloaders.base import BaseDownloader, DownloadCallback
        from core.models.novel import Novel, create_novel_from_api_response
        from core.models.chapter import Chapter, create_chapters_from_list
        from utils.network_utils import make_request, create_session_with_retries


class NovelDownloader(BaseDownloader):
    """小说下载器主类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        初始化下载器
        
        Args:
            config: 配置字典
            **kwargs: 其他参数
        """
        # 默认配置
        default_config = {
            'max_workers': 4,
            'request_timeout': 15,
            'max_retries': 3,
            'rate_limit': 0.5,
            'api_endpoints': [],
            'auth_token': '',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            max_workers=default_config['max_workers'],
            request_timeout=default_config['request_timeout'],
            max_retries=default_config['max_retries'],
            rate_limit=default_config['rate_limit']
        )
        
        self.config = default_config
        self.session = create_session_with_retries(self.max_retries)
        self.session.headers.update({
            'User-Agent': self.config['user_agent']
        })
        
        # API端点
        self.api_endpoints = self.config.get('api_endpoints', [])
        self.current_api_index = 0
    
    def get_novel_info(self, book_id: str) -> Novel:
        """
        获取小说信息
        
        Args:
            book_id: 小说ID
            
        Returns:
            Novel: 小说对象
        """
        # 这里应该调用实际的API获取小说信息
        # 为了演示，我创建一个基本的小说对象
        
        # 尝试从API获取信息
        novel_data = self._fetch_novel_info_from_api(book_id)
        
        if novel_data:
            novel = create_novel_from_api_response(novel_data)
        else:
            # 如果API失败，创建基本的小说对象
            novel = Novel(
                book_id=book_id,
                title=f"小说_{book_id}",
                author="未知作者",
                description="暂无简介"
            )
        
        return novel
    
    def get_chapter_list(self, novel: Novel) -> List[Chapter]:
        """
        获取章节列表
        
        Args:
            novel: 小说对象
            
        Returns:
            List[Chapter]: 章节列表
        """
        # 尝试从API获取章节列表
        chapters_data = self._fetch_chapters_from_api(novel.book_id)
        
        if chapters_data:
            chapters = create_chapters_from_list(chapters_data)
        else:
            # 如果API失败，创建空的章节列表
            chapters = []
        
        return chapters
    
    def download_chapter_content(self, chapter: Chapter) -> str:
        """
        下载章节内容
        
        Args:
            chapter: 章节对象
            
        Returns:
            str: 章节内容
        """
        # 尝试从API获取章节内容
        content = self._fetch_chapter_content_from_api(chapter.chapter_id)
        
        if not content:
            raise ValueError(f"无法获取章节内容: {chapter.title}")
        
        return content
    
    def _fetch_novel_info_from_api(self, book_id: str) -> Optional[Dict[str, Any]]:
        """从API获取小说信息"""
        for api_endpoint in self.api_endpoints:
            try:
                url = f"{api_endpoint}/novel/{book_id}"
                response = self.session.get(url, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        return data.get('data')
                        
            except Exception as e:
                print(f"API请求失败 {api_endpoint}: {e}")
                continue
        
        return None
    
    def _fetch_chapters_from_api(self, book_id: str) -> Optional[List[Dict[str, Any]]]:
        """从API获取章节列表"""
        for api_endpoint in self.api_endpoints:
            try:
                url = f"{api_endpoint}/chapters/{book_id}"
                response = self.session.get(url, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        return data.get('data', [])
                        
            except Exception as e:
                print(f"获取章节列表失败 {api_endpoint}: {e}")
                continue
        
        return None
    
    def _fetch_chapter_content_from_api(self, chapter_id: str) -> Optional[str]:
        """从API获取章节内容"""
        for api_endpoint in self.api_endpoints:
            try:
                url = f"{api_endpoint}/chapter/{chapter_id}"
                response = self.session.get(url, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        return data.get('data', {}).get('content', '')
                        
            except Exception as e:
                print(f"获取章节内容失败 {api_endpoint}: {e}")
                continue
        
        return None
    
    def add_api_endpoint(self, endpoint: str):
        """添加API端点"""
        if endpoint not in self.api_endpoints:
            self.api_endpoints.append(endpoint)
    
    def remove_api_endpoint(self, endpoint: str):
        """移除API端点"""
        if endpoint in self.api_endpoints:
            self.api_endpoints.remove(endpoint)
    
    def test_api_endpoints(self) -> Dict[str, bool]:
        """测试API端点可用性"""
        results = {}
        for endpoint in self.api_endpoints:
            try:
                response = self.session.get(f"{endpoint}/health", timeout=5)
                results[endpoint] = response.status_code == 200
            except Exception:
                results[endpoint] = False
        
        return results
    
    def get_working_endpoints(self) -> List[str]:
        """获取可用的API端点"""
        test_results = self.test_api_endpoints()
        return [endpoint for endpoint, working in test_results.items() if working]
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        
        # 更新基础参数
        if 'max_workers' in config:
            self.max_workers = config['max_workers']
        if 'request_timeout' in config:
            self.request_timeout = config['request_timeout']
        if 'max_retries' in config:
            self.max_retries = config['max_retries']
        if 'rate_limit' in config:
            self.rate_limit = config['rate_limit']
        
        # 更新API端点
        if 'api_endpoints' in config:
            self.api_endpoints = config['api_endpoints']
        
        # 更新请求头
        if 'user_agent' in config:
            self.session.headers.update({'User-Agent': config['user_agent']})


# 便捷函数
def create_downloader_from_config(config: Dict[str, Any]) -> NovelDownloader:
    """从配置创建下载器"""
    return NovelDownloader(config)


__all__ = ["NovelDownloader", "create_downloader_from_config"]
