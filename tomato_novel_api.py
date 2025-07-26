#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
番茄小说API调用脚本
可以独立运行或作为模块调用
"""

import requests
import json
import sys
import urllib.parse
import time
from typing import Optional


class TomatoNovelAPI:
    def __init__(self):
        self.base_url = "http://read.tutuxka.top"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': self.base_url,
            'DNT': '1'
        })
        # 设置默认超时时间
        self.timeout = 30
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2

    def _make_request_with_retry(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        带重试机制的请求方法
        
        Args:
            url (str): 请求URL
            params (dict, optional): 请求参数
            
        Returns:
            dict: 响应结果
        """
        for attempt in range(self.max_retries):
            try:
                print(f"尝试请求 (第{attempt + 1}次): {url}")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                print(f"请求超时 (第{attempt + 1}次)")
                if attempt < self.max_retries - 1:
                    print(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"请求超时，已达到最大重试次数 ({self.max_retries})")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 504:
                    print(f"服务器网关超时 (504) - 第{attempt + 1}次")
                    if attempt < self.max_retries - 1:
                        print(f"等待 {self.retry_delay * 2} 秒后重试...")
                        time.sleep(self.retry_delay * 2)  # 504错误等待更长时间
                    else:
                        print(f"服务器持续超时，建议稍后再试")
                else:
                    print(f"HTTP错误: {e}")
                    break  # 其他HTTP错误不重试
                    
            except requests.RequestException as e:
                print(f"网络请求失败: {e}")
                if attempt < self.max_retries - 1:
                    print(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"网络连接失败，已达到最大重试次数")
                    
            except json.JSONDecodeError as e:
                print(f"解析响应JSON失败: {e}")
                break  # JSON解析错误不重试
                
        return None
    
    def search_novels(self, keyword, offset=0, tab_type=1):
        """
        搜索小说
        
        Args:
            keyword (str): 搜索关键词
            offset (int): 偏移量，默认为0
            tab_type (int): 标签类型，默认为1
            
        Returns:
            dict: 搜索结果
        """
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"{self.base_url}/search.php?key={encoded_keyword}&offset={offset}&tab_type={tab_type}"
        return self._make_request_with_retry(url)

    def get_novel_info(self, book_id):
        """
        获取小说信息
        
        Args:
            book_id (str): 小说ID
            
        Returns:
            dict: 小说信息
        """
        url = f"{self.base_url}/content.php?book_id={book_id}"
        return self._make_request_with_retry(url)

    def get_chapter_content(self, item_ids):
        """
        获取章节内容
        
        Args:
            item_ids (str): 章节ID
            
        Returns:
            dict: 章节内容
        """
        url = f"{self.base_url}/content.php?item_ids={item_ids}&api_type=full"
        return self._make_request_with_retry(url)

    def get_book_details(self, bookId):
        """
        获取书籍详细信息
        
        Args:
            bookId (str): 书籍ID
            
        Returns:
            dict: 书籍详细信息
        """
        url = f"{self.base_url}/book.php?bookId={bookId}"
        return self._make_request_with_retry(url)

    def download_full_novel(self, book_id, item_ids):
        """
        一次性下载整本小说
        
        Args:
            book_id (str): 小说ID
            item_ids (list or str): 章节ID列表或逗号分隔的章节ID字符串
            
        Returns:
            dict: 小说完整内容
        """
        # 如果item_ids是列表，则转换为逗号分隔的字符串
        if isinstance(item_ids, list):
            item_ids_str = ','.join(item_ids)
        else:
            item_ids_str = item_ids
            
        url = f"{self.base_url}/full.php?book_id={book_id}&item_ids={item_ids_str}"
        
        result = self._make_request_with_retry(url)
        if result:
            # 检查返回结果是否为列表类型（full.php接口返回的是列表）
            if not isinstance(result, list):
                print(f"下载整本小说失败，服务器返回了非列表类型: {type(result)}")
                return None
            # full.php接口直接返回章节内容列表，不需要检查success字段
            return {"success": True, "data": {"items": result}}
        return None


def main():
    """主函数，用于独立运行脚本"""
    api = TomatoNovelAPI()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  搜索小说: python tomato_novel_api.py search <关键词>")
        print("  获取小说信息: python tomato_novel_api.py novel_info <书籍ID>")
        print("  获取书籍详细信息: python tomato_novel_api.py book_details <书籍ID>")
        print("  获取章节内容: python tomato_novel_api.py chapter_content <章节ID>")
        print("  下载整本小说: python tomato_novel_api.py download_full <书籍ID> <章节ID列表>")
        return
    
    command = sys.argv[1]
    
    if command == "search":
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            return
        
        keyword = sys.argv[2]
        print(f"正在搜索: {keyword}")
        result = api.search_novels(keyword)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("搜索失败")
            
    elif command == "novel_info":
        if len(sys.argv) < 3:
            print("请提供书籍ID")
            return
            
        book_id = sys.argv[2]
        print(f"正在获取书籍信息: {book_id}")
        result = api.get_novel_info(book_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("获取书籍信息失败")
            
    elif command == "book_details":
        if len(sys.argv) < 3:
            print("请提供书籍ID")
            return
            
        bookId = sys.argv[2]
        print(f"正在获取书籍详细信息: {bookId}")
        result = api.get_book_details(bookId)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("获取书籍详细信息失败")
            
    elif command == "chapter_content":
        if len(sys.argv) < 3:
            print("请提供章节ID")
            return
            
        item_ids = sys.argv[2]
        print(f"正在获取章节内容: {item_ids}")
        result = api.get_chapter_content(item_ids)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("获取章节内容失败")
            
    elif command == "download_full":
        if len(sys.argv) < 4:
            print("请提供书籍ID和章节ID列表")
            return
            
        book_id = sys.argv[2]
        item_ids = sys.argv[3]
        print(f"正在下载整本小说: {book_id}")
        result = api.download_full_novel(book_id, item_ids)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("下载整本小说失败")
            
    else:
        print(f"未知命令: {command}")
        print("支持的命令: search, novel_info, book_details, chapter_content, download_full")


# 当脚本被直接运行时执行主函数
if __name__ == "__main__":
    main()