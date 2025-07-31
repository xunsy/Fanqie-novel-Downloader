# -*- coding: utf-8 -*-
"""
内容处理模块
负责章节内容的解析、处理和格式化
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
try:
    from config import Config
    from network import NetworkManager
except ImportError:
    # 提供基本配置作为后备
    class Config:
        BATCH_CONFIG = {
            "enabled": True,
            "max_batch_size": 290,
            "timeout": 10,
            "name": "qyuing",
            "batch_endpoint": None,
            "token": None
        }
    
    class NetworkManager:
        def __init__(self):
            pass
        
        def get_headers(self):
            return {}
        
        def make_request(self, *args, **kwargs):
            return None


class ContentProcessor:
    """内容处理器"""
    
    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager
        self.config = Config()
    
    def extract_chapters(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从HTML中提取章节信息"""
        chapters = []
        
        # 查找章节链接
        chapter_links = soup.find_all('a', href=True)
        
        for link in chapter_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # 检查是否为章节链接
            if self._is_chapter_link(href, title):
                chapter_id = self._extract_chapter_id(href)
                if chapter_id:
                    chapters.append({
                        'id': chapter_id,
                        'title': title,
                        'url': href
                    })
        
        return chapters
    
    def _is_chapter_link(self, href: str, title: str) -> bool:
        """判断是否为章节链接"""
        # 检查URL模式
        chapter_patterns = [
            r'/chapter/',
            r'/read/',
            r'chapter_id=',
            r'chapterId='
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return True
        
        # 检查标题模式
        title_patterns = [
            r'第\s*\d+\s*章',
            r'chapter\s*\d+',
            r'第\s*[一二三四五六七八九十百千万]+\s*章'
        ]
        
        for pattern in title_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_chapter_id(self, href: str) -> Optional[str]:
        """从URL中提取章节ID"""
        # 尝试不同的ID提取模式
        patterns = [
            r'chapter_id=(\d+)',
            r'chapterId=(\d+)',
            r'/chapter/(\d+)',
            r'/read/(\d+)',
            r'id=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        
        return None
    
    def process_chapter_content(self, content: str) -> str:
        """处理章节内容，清理和格式化"""
        if not content:
            return ""
        
        # 移除HTML标签
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # 清理文本
        text = self._clean_text(text)
        
        # 格式化段落
        text = self._format_paragraphs(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符和广告文本
        unwanted_patterns = [
            r'本章未完.*?点击下一页继续阅读',
            r'请收藏本站：.*?手机版阅读网址：',
            r'一秒记住.*?为您提供精彩小说阅读',
            r'天才一秒记住.*?地址：',
            r'笔趣阁.*?最快更新',
            r'www\.[^。]*?\.com',
            r'http[s]?://[^\s]*',
            r'【.*?】',
            r'（.*?广告.*?）',
            r'\(.*?广告.*?\)',
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除多余的标点符号
        text = re.sub(r'[。]{2,}', '。', text)
        text = re.sub(r'[，]{2,}', '，', text)
        text = re.sub(r'[！]{2,}', '！', text)
        text = re.sub(r'[？]{2,}', '？', text)
        
        return text.strip()
    
    def _format_paragraphs(self, text: str) -> str:
        """格式化段落"""
        # 按句号分割并重新组织段落
        sentences = re.split(r'[。！？]', text)
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            current_paragraph.append(sentence)
            
            # 每3-5句组成一个段落
            if len(current_paragraph) >= 3:
                paragraphs.append('。'.join(current_paragraph) + '。')
                current_paragraph = []
        
        # 处理剩余的句子
        if current_paragraph:
            paragraphs.append('。'.join(current_paragraph) + '。')
        
        return '\n\n'.join(paragraphs)
    
    def batch_download_chapters(self, item_ids: List[str], headers: Dict[str, str]) -> Dict[str, str]:
        """批量下载章节内容"""
        results = {}
        
        if not item_ids:
            return results
        
        # 检查是否支持批量下载
        if self.config.BATCH_CONFIG['enabled'] and len(item_ids) > 1:
            try:
                batch_results = self._batch_download_via_api(item_ids, headers)
                if batch_results:
                    return batch_results
            except Exception as e:
                print(f"批量下载失败，回退到单个下载: {e}")
        
        # 单个下载
        for item_id in item_ids:
            try:
                content = self._download_single_chapter(item_id, headers)
                if content:
                    results[item_id] = content
            except Exception as e:
                print(f"下载章节 {item_id} 失败: {e}")
                results[item_id] = ""
        
        return results
    
    def _batch_download_via_api(self, item_ids: List[str], headers: Dict[str, str]) -> Dict[str, str]:
        """通过API批量下载"""
        batch_config = self.config.BATCH_CONFIG
        
        if not batch_config['batch_endpoint']:
            return {}
        
        # 分批处理
        max_batch_size = batch_config['max_batch_size']
        results = {}
        
        for i in range(0, len(item_ids), max_batch_size):
            batch_ids = item_ids[i:i + max_batch_size]
            
            data = {
                'name': batch_config['name'],
                'data': batch_ids
            }
            
            if batch_config['token']:
                data['token'] = batch_config['token']
            
            try:
                response = self.network_manager.make_request(
                    batch_config['batch_endpoint'],
                    method='POST',
                    headers=headers,
                    data=data,
                    timeout=batch_config['timeout']
                )
                
                if response and response.get('code') == 0:
                    batch_results = response.get('data', {})
                    for item_id, content in batch_results.items():
                        if content:
                            processed_content = self.process_chapter_content(content)
                            results[item_id] = processed_content
                
            except Exception as e:
                print(f"批量下载批次失败: {e}")
                continue
        
        return results
    
    def _download_single_chapter(self, item_id: str, headers: Dict[str, str]) -> str:
        """下载单个章节"""
        # 这里应该调用具体的下载逻辑
        # 由于需要访问API端点，这部分逻辑会在download_engine中实现
        return ""
    
    def extract_book_info_from_html(self, html_content: str) -> Dict[str, Any]:
        """从HTML中提取书籍信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        book_info = {}
        
        # 提取标题
        title_selectors = [
            'h1',
            '.book-title',
            '.title',
            '[class*="title"]',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                book_info['title'] = title_elem.get_text(strip=True)
                break
        
        # 提取作者
        author_selectors = [
            '.author',
            '[class*="author"]',
            '.writer',
            '[class*="writer"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                book_info['author'] = author_elem.get_text(strip=True)
                break
        
        # 提取简介
        intro_selectors = [
            '.intro',
            '.introduction',
            '.summary',
            '[class*="intro"]',
            '[class*="summary"]'
        ]
        
        for selector in intro_selectors:
            intro_elem = soup.select_one(selector)
            if intro_elem:
                book_info['introduction'] = intro_elem.get_text(strip=True)
                break
        
        # 提取封面
        cover_selectors = [
            'img[class*="cover"]',
            '.cover img',
            '.book-cover img',
            'img[alt*="封面"]'
        ]
        
        for selector in cover_selectors:
            cover_elem = soup.select_one(selector)
            if cover_elem:
                book_info['cover_url'] = cover_elem.get('src', '')
                break
        
        return book_info