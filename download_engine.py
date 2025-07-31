# -*- coding: utf-8 -*-
"""
下载引擎模块
负责核心下载逻辑、章节获取、书籍信息获取等功能
"""

import requests
import bs4
import time
try:
    from config import CONFIG
    from network import NetworkManager
    from content_processor import ContentProcessor
except ImportError:
    # 提供基本配置作为后备
    CONFIG = {
        "batch_config": {
            "enabled": True,
            "name": "qyuing"
        }
    }
    NetworkManager = None
    ContentProcessor = None


class DownloadEngine:
    """下载引擎类，负责核心下载逻辑"""
    
    def __init__(self, network_manager=None, content_processor=None, progress_callback=None):
        self.progress_callback = progress_callback
        self.network_manager = network_manager or NetworkManager()
        self.content_processor = content_processor or ContentProcessor(self.network_manager)
    
    def log(self, message):
        """日志输出"""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def down_text(self, chapter_id, headers, book_id=None):
        """
        下载章节内容，支持多个API源
        返回: (title, content) 或 (None, None)
        """
        apis = [
            ("fanqie_sdk", f"https://novel.snssdk.com/api/novel/book/reader/full/v1/?device_platform=android&parent_id=0&aid=2329&platform_id=1&group_id={chapter_id}&item_id={chapter_id}"),
            ("fqweb", f"http://fqweb.jsj66.com/content?item_id={chapter_id}"),
            ("qyuing", f"https://novel.snssdk.com/api/novel/book/reader/full/v1/?device_platform=android&parent_id=0&aid=2329&platform_id=1&group_id={chapter_id}&item_id={chapter_id}"),
            ("lsjk", f"https://novel.snssdk.com/api/novel/book/reader/full/v1/?device_platform=android&parent_id=0&aid=2329&platform_id=1&group_id={chapter_id}&item_id={chapter_id}")
        ]
        
        for api_name, url in apis:
            try:
                if api_name == "qyuing" and CONFIG["batch_config"]["enabled"]:
                    # 使用批量下载
                    batch_result = self.content_processor.batch_download_chapters([chapter_id], headers)
                    if batch_result and chapter_id in batch_result:
                        content = batch_result[chapter_id]
                        processed_content = self.content_processor.process_chapter_content(content)
                        return f"章节{chapter_id}", processed_content
                
                # 单个章节下载
                response = self.network_manager.make_request(url, headers=headers)
                if not response:
                    continue
                
                data = response.json()
                
                if api_name == "fanqie_sdk":
                    if data.get("code") == 0 and "data" in data:
                        content = data["data"]["content"]
                        processed_content = self.content_processor.process_chapter_content(content)
                        return data["data"].get("title", f"章节{chapter_id}"), processed_content
                
                elif api_name == "fqweb":
                    if data.get("isSuccess") and data.get("data", {}).get("code") == "0":
                        chapter_data = data["data"]["data"]
                        content = chapter_data["content"]
                        processed_content = self.content_processor.process_chapter_content(content)
                        return chapter_data.get("title", f"章节{chapter_id}"), processed_content
                
                elif api_name in ["qyuing", "lsjk"]:
                    if data.get("code") == 0 and "data" in data:
                        content = data["data"]["content"]
                        processed_content = self.content_processor.process_chapter_content(content)
                        return data["data"].get("title", f"章节{chapter_id}"), processed_content
                
            except Exception as e:
                self.log(f"API {api_name} 请求失败: {str(e)}")
                continue
        
        return None, None
    
    def get_chapters_from_api(self, book_id, headers):
        """从API获取章节列表"""
        try:
            page_url = f'https://fanqienovel.com/page/{book_id}'
            response = self.network_manager.make_request(page_url, headers=headers)
            if not response:
                return None
            
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            chapters = self.content_processor.extract_chapters(soup)
            
            api_url = f"https://fanqienovel.com/api/reader/directory/detail?bookId={book_id}"
            api_response = self.network_manager.make_request(api_url, headers=headers)
            if not api_response:
                return chapters
            
            api_data = api_response.json()
            chapter_ids = api_data.get("data", {}).get("allItemIds", [])
            
            final_chapters = []
            for idx, chapter_id in enumerate(chapter_ids):
                web_chapter = next((ch for ch in chapters if ch["id"] == chapter_id), None)
                
                if web_chapter:
                    final_chapters.append({
                        "id": chapter_id,
                        "title": web_chapter["title"],
                        "index": idx
                    })
                else:
                    final_chapters.append({
                        "id": chapter_id,
                        "title": f"第{idx+1}章",
                        "index": idx
                    })
            
            return final_chapters
        except Exception as e:
            self.log(f"获取章节列表失败: {str(e)}")
            return None
    
    def get_book_info(self, book_id, headers):
        """获取书名、作者、简介"""
        url = f'https://fanqienovel.com/page/{book_id}'
        try:
            response = self.network_manager.make_request(url, headers=headers)
            if not response:
                return None, None, None

            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            
            name_element = soup.find('h1')
            name = name_element.text if name_element else "未知书名"
            
            author_name = "未知作者"
            author_name_element = soup.find('div', class_='author-name')
            if author_name_element:
                author_name_span = author_name_element.find('span', class_='author-name-text')
                if author_name_span:
                    author_name = author_name_span.text
            
            description = "无简介"
            description_element = soup.find('div', class_='page-abstract-content')
            if description_element:
                description_p = description_element.find('p')
                if description_p:
                    description = description_p.text
            
            return name, author_name, description
        except Exception as e:
            self.log(f"获取书籍信息失败: {str(e)}")
            return None, None, None
    
    def get_book_info_enhanced(self, book_id, headers):
        """
        使用fqweb API获取详细书籍信息
        返回比网页爬取更丰富的信息
        """
        try:
            url = f"http://fqweb.jsj66.com/info?book_id={book_id}"
            response = self.network_manager.make_request(url, headers=headers)
            if not response:
                return None
            
            data = response.json()
            
            # 检查响应格式
            if not data.get('isSuccess') or data.get('data', {}).get('code') != '0':
                self.log("API返回错误信息")
                return None
            
            book_data = data['data']['data']
            
            # 构造增强的书籍信息
            enhanced_info = {
                'book_id': book_data.get('book_id', book_id),
                'book_name': book_data.get('book_name', '未知书名'),
                'author': book_data.get('author', '未知作者'),
                'author_id': book_data.get('author_id', ''),
                'abstract': book_data.get('abstract', '无简介'),
                'category': book_data.get('category', '未知分类'),
                'tags': book_data.get('tags', ''),
                'score': book_data.get('score', '0'),
                'word_number': book_data.get('word_number', '0'),
                'serial_count': book_data.get('serial_count', '0'),
                'creation_status': book_data.get('creation_status', '0'),  # 0=完结, 1=连载
                'read_count': book_data.get('read_count', '0'),
                'thumb_url': book_data.get('thumb_url', ''),
                'source': '番茄小说',
                'first_chapter_title': book_data.get('first_chapter_title', ''),
                'last_chapter_title': book_data.get('last_chapter_title', ''),
                'last_chapter_update_time': book_data.get('last_chapter_update_time', ''),
                'create_time': book_data.get('create_time', ''),
                'copyright_info': book_data.get('copyright_info', ''),
                'role': book_data.get('role', ''),  # 主角名
                
                # 作者信息
                'author_info': book_data.get('author_info', {}),
                
                # 标签详细信息
                'title_page_tags': book_data.get('title_page_tags', []),
                
                # 其他详细信息
                'genre': book_data.get('genre', '0'),
                'gender': book_data.get('gender', '1'),
                'exclusive': book_data.get('exclusive', '0'),
                'for_young': book_data.get('for_young', False),
                'platform': book_data.get('platform', '2'),
            }
            
            return enhanced_info
            
        except Exception as e:
            self.log(f"获取增强书籍信息失败: {str(e)}")
            return None