#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强型番茄小说下载器
集成参考代码的功能，支持GUI进度回调
"""

import time
import requests
import bs4
import re
import os
import random
import json
import urllib3
import threading
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from collections import OrderedDict
from fake_useragent import UserAgent
from typing import Optional, Dict, Callable
from ebooklib import epub
import base64
import gzip
from urllib.parse import urlencode

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# 全局配置
CONFIG = {
    "max_workers": 4,
    "max_retries": 3,
    "request_timeout": 15,
    "status_file": "chapter.json",
    "request_rate_limit": 0.4,
    "auth_token": "wcnmd91jb",
    "server_url": "https://dlbkltos.s7123.xyz:5080/api/sources",
    "api_endpoints": [],
    "batch_config": {
        "name": "qyuing",
        "base_url": None,
        "batch_endpoint": None,
        "token": None,
        "max_batch_size": 290,
        "timeout": 10,
        "enabled": True
    }
}

class EnhancedNovelDownloader:
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        初始化增强型下载器
        
        Args:
            progress_callback: 进度回调函数 (progress, message)
        """
        self.progress_callback = progress_callback
        self.downloaded = set()
        self.chapter_results = {}
        self.lock = threading.Lock()
        self.is_cancelled = False
        
        # 初始化API端点
        self.fetch_api_endpoints_from_server()
    
    def log(self, message: str):
        """记录日志"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        if self.progress_callback:
            # 不改变进度，只更新消息
            self.progress_callback(-1, message)
    
    def update_progress(self, progress: float, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def make_request(self, url, headers=None, params=None, data=None, method='GET', verify=False, timeout=None):
        """通用的请求函数"""
        if headers is None:
            headers = self.get_headers()
        
        try:
            request_params = {
                'headers': headers,
                'params': params,
                'verify': verify,
                'timeout': timeout if timeout is not None else CONFIG["request_timeout"]
            }
            
            if data:
                request_params['json'] = data

            session = requests.Session()
            if method.upper() == 'GET':
                response = session.get(url, **request_params)
            elif method.upper() == 'POST':
                response = session.post(url, **request_params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            return response
        except Exception as e:
            self.log(f"请求失败: {str(e)}")
            raise

    def get_headers(self) -> Dict[str, str]:
        """生成随机请求头"""
        browsers = ['chrome', 'edge']
        browser = random.choice(browsers)
        
        if browser == 'chrome':
            user_agent = UserAgent().chrome
        else:
            user_agent = UserAgent().edge
        
        return {
            "User-Agent": user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://fanqienovel.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }

    def fetch_api_endpoints_from_server(self):
        """从服务器获取API列表"""
        try:
            headers = self.get_headers()
            headers["X-Auth-Token"] = CONFIG["auth_token"]
            
            response = requests.get(
                CONFIG["server_url"],
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = data.get("sources", [])
                
                CONFIG["api_endpoints"] = []
                
                for source in sources:
                    if source["enabled"]:
                        if source["name"] == CONFIG["batch_config"]["name"]:
                            base_url = source["single_url"].split('?')[0]
                            batch_endpoint = base_url.split('/')[-1]
                            base_url = base_url.rsplit('/', 1)[0] if '/' in base_url else base_url
                            
                            CONFIG["batch_config"]["base_url"] = base_url
                            CONFIG["batch_config"]["batch_endpoint"] = f"/{batch_endpoint}"
                            CONFIG["batch_config"]["token"] = source.get("token", "")
                            CONFIG["batch_config"]["enabled"] = True
                        else:
                            endpoint = {"url": source["single_url"], "name": source["name"]}
                            if source["name"] == "fanqie_sdk":
                                endpoint["params"] = source.get("params", {})
                                endpoint["data"] = source.get("data", {})
                            CONFIG["api_endpoints"].append(endpoint)
                
                self.log("成功从服务器获取API列表!")
                return True
            else:
                self.log(f"获取API列表失败，状态码: {response.status_code}")
        except Exception as e:
            self.log(f"获取API列表异常: {str(e)}")

    def extract_chapters(self, soup):
        """解析章节列表"""
        chapters = []
        for idx, item in enumerate(soup.select('div.chapter-item')):
            a_tag = item.find('a')
            if not a_tag:
                continue
            
            raw_title = a_tag.get_text(strip=True)
            
            if re.match(r'^(番外|特别篇|if线)\s*', raw_title):
                final_title = raw_title
            else:
                clean_title = re.sub(
                    r'^第[一二三四五六七八九十百千\d]+章\s*',
                    '', 
                    raw_title
                ).strip()
                final_title = f"第{idx+1}章 {clean_title}"
            
            chapters.append({
                "id": a_tag['href'].split('/')[-1],
                "title": final_title,
                "url": f"https://fanqienovel.com{a_tag['href']}",
                "index": idx
            })
        return chapters

    def batch_download_chapters(self, item_ids, headers):
        """批量下载章节内容"""
        if not CONFIG["batch_config"]["enabled"] or CONFIG["batch_config"]["name"] != "qyuing":
            self.log("批量下载功能仅限qyuing API")
            return None
            
        batch_config = CONFIG["batch_config"]
        url = f"{batch_config['base_url']}{batch_config['batch_endpoint']}"
        
        try:
            batch_headers = headers.copy()
            if batch_config["token"]:
                batch_headers["token"] = batch_config["token"]
            batch_headers["Content-Type"] = "application/json"
            
            payload = {"item_ids": item_ids}
            response = self.make_request(
                url,
                headers=batch_headers,
                method='POST',
                data=json.dumps(payload),
                timeout=batch_config["timeout"],
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
            else:
                self.log(f"批量下载失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"批量下载异常！")
            return None

    def process_chapter_content(self, content):
        """处理章节内容"""
        if not content or not isinstance(content, str):
            return ""
        
        try:
            paragraphs = []
            if '<p idx=' in content:
                paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content, re.DOTALL)
            else:
                paragraphs = content.split('\n')
            
            if paragraphs:
                first_para = paragraphs[0].strip()
                if not first_para.startswith('    '):
                    paragraphs[0] = '    ' + first_para
            
            cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
            formatted_content = '\n'.join('    ' + line if line.strip() else line 
                                        for line in cleaned_content.split('\n'))
            
            formatted_content = re.sub(r'<header>.*?</header>', '', formatted_content, flags=re.DOTALL)
            formatted_content = re.sub(r'<footer>.*?</footer>', '', formatted_content, flags=re.DOTALL)
            formatted_content = re.sub(r'</?article>', '', formatted_content)
            formatted_content = re.sub(r'<[^>]+>', '', formatted_content)
            formatted_content = re.sub(r'\\u003c|\\u003e', '', formatted_content)
            
            # 压缩多余的空行
            formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content).strip()
            return formatted_content
        except Exception as e:
            self.log(f"内容处理错误: {str(e)}")
            return str(content)

    def down_text(self, chapter_id, headers, book_id=None):
        """下载章节内容"""
        content = ""
        chapter_title = ""
        first_error_printed = False

        if not hasattr(self.down_text, "api_status"):
            self.down_text.api_status = {endpoint["url"]: {
                "last_response_time": float('inf'),
                "error_count": 0,
                "last_try_time": 0
            } for endpoint in CONFIG["api_endpoints"]}

        # 记录未成功的id
        failed_chapter_id = chapter_id
        
        for idx, endpoint in enumerate(CONFIG["api_endpoints"]):
            if self.is_cancelled:
                return None, None
                
            current_endpoint = endpoint["url"]
            api_name = endpoint["name"]
            
            self.down_text.api_status[endpoint["url"]]["last_try_time"] = time.time()
            
            try:
                time.sleep(random.uniform(0.1, 0.5))
                start_time = time.time()
                
                if api_name == "fanqie_sdk":
                    params = endpoint.get("params", {
                        "sdk_type": "4",
                        "novelsdk_aid": "638505"
                    })
                    data = endpoint.get("data", {
                        "item_id": chapter_id,
                        "need_book_info": 1,
                        "show_picture": 1,
                        "sdk_type": 1
                    })
                    data["item_id"] = chapter_id
                    
                    response = self.make_request(
                        current_endpoint,
                        headers=headers.copy(),
                        params=params,
                        method='POST',
                        data=data,
                        timeout=CONFIG["request_timeout"],
                        verify=False
                    )
                else:
                    current_endpoint = endpoint["url"].format(chapter_id=failed_chapter_id)
                    response = self.make_request(
                        current_endpoint, 
                        headers=headers.copy(),
                        timeout=CONFIG["request_timeout"],
                        verify=False
                    )
                
                response_time = time.time() - start_time
                self.down_text.api_status[endpoint["url"]].update({
                    "last_response_time": response_time,
                    "error_count": max(0, self.down_text.api_status[endpoint["url"]]["error_count"] - 1)
                })
                
                data = response.json()
                
                if api_name == "fanqie_sdk":
                    content = data.get("data", {}).get("content", "")
                    chapter_title = data.get("data", {}).get("title", "")
                    if content:
                        processed_content = self.process_chapter_content(content)
                        processed_content = re.sub(r'^(\s*)', r'    ', processed_content, flags=re.MULTILINE)
                        return chapter_title, processed_content
                elif api_name == "lsjk" and content:
                    paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                    cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                    formatted_content = '\n'.join('    ' + line if line.strip() else line 
                                                for line in cleaned_content.split('\n'))
                    return chapter_title, formatted_content
                elif api_name == "qyuing" and data.get("code") == 0 and content:
                    processed_content = self.process_chapter_content(content)
                    return chapter_title, processed_content
                elif api_name == "fqweb":
                    if data.get("data", {}).get("code") in ["0", 0]:
                        content = data.get("data", {}).get("data", {}).get("content", "")
                        if content:
                            processed_content = self.process_chapter_content(content)
                            processed_content = re.sub(r'^(\s*)', r'    ', processed_content, flags=re.MULTILINE)                        
                            return "", processed_content

                if not first_error_printed:
                    self.log(f"API：{api_name}错误，无法下载章节，正在重试")
                    first_error_printed = True
                self.down_text.api_status[endpoint["url"]]["error_count"] += 1
            except Exception as e:
                if not first_error_printed:
                    self.log(f"API：{api_name}错误，无法下载章节，正在重试")
                    first_error_printed = True
                self.down_text.api_status[endpoint["url"]]["error_count"] += 1
                time.sleep(3)
            
            if idx < len(CONFIG["api_endpoints"]) - 1:
                self.log("正在切换到下一个api")
        
        self.log(f"所有API尝试失败，无法下载章节 {chapter_id}")
        return None, None

    def get_chapters_from_api(self, book_id, headers):
        """从API获取章节列表"""
        try:
            page_url = f'https://fanqienovel.com/page/{book_id}'
            response = requests.get(page_url, headers=headers, timeout=CONFIG["request_timeout"])
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            chapters = self.extract_chapters(soup)  
            
            api_url = f"https://fanqienovel.com/api/reader/directory/detail?bookId={book_id}"
            api_response = requests.get(api_url, headers=headers, timeout=CONFIG["request_timeout"])
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

    def create_epub_book(self, name, author_name, description, chapter_results, chapters):
        """创建EPUB文件"""
        book = epub.EpubBook()
        book.set_identifier(f'book_{name}_{int(time.time())}')
        book.set_title(name)
        book.set_language('zh-CN')
        book.add_author(author_name)
        book.add_metadata('DC', 'description', description)
        
        book.toc = []
        spine = ['nav']
        
        for idx in range(len(chapters)):
            if idx in chapter_results:
                result = chapter_results[idx]
                title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chap_{idx}.xhtml',
                    lang='zh-CN'
                )
                content = result['content'].replace('\n', '<br/>')
                chapter.content = f'<h1>{title}</h1><p>{content}</p>'.encode('utf-8')
                book.add_item(chapter)
                book.toc.append(chapter)
                spine.append(chapter)
        
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        
        return book

    def download_chapter(self, chapter, headers, save_path, book_name, downloaded, book_id, file_format='txt'):
        """下载单个章节"""
        if chapter["id"] in downloaded:
            return None
        
        title, content = self.down_text(chapter["id"], headers, book_id)
        
        if content:
            if file_format == 'txt':
                output_file_path = os.path.join(save_path, f"{book_name}.txt")
                try:
                    with open(output_file_path, 'a', encoding='utf-8') as f:
                        f.write(f'{chapter["title"]}\n')
                        f.write(content + '\n\n')
                    
                    downloaded.add(chapter["id"])
                    self.save_status(save_path, downloaded)
                    return chapter["index"], content
                except Exception as e:
                    self.log(f"写入文件失败: {str(e)}")
            return chapter["index"], content
        return None

    def get_book_info(self, book_id, headers):
        """获取书名、作者、简介"""
        url = f'https://fanqienovel.com/page/{book_id}'
        try:
            response = requests.get(url, headers=headers, timeout=CONFIG["request_timeout"])
            if response.status_code != 200:
                self.log(f"网络请求失败，状态码: {response.status_code}")
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

    def load_status(self, save_path):
        """加载下载状态"""
        status_file = os.path.join(save_path, CONFIG["status_file"])
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data)
                    return set()
            except:
                pass
        return set()

    def save_status(self, save_path, downloaded):
        """保存下载状态"""
        status_file = os.path.join(save_path, CONFIG["status_file"])
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(list(downloaded), f, ensure_ascii=False, indent=2)

    def cancel_download(self):
        """取消下载"""
        self.is_cancelled = True
        self.log("用户取消下载")

    def run_download(self, book_id, save_path, file_format='txt', start_chapter=None, end_chapter=None):
        """
        运行下载
        
        Args:
            book_id: 书籍ID
            save_path: 保存路径
            file_format: 文件格式 ('txt' 或 'epub')
            start_chapter: 起始章节（可选，从0开始）
            end_chapter: 结束章节（可选，包含）
        """
        self.is_cancelled = False
        self.downloaded = set()
        self.chapter_results = {}
        
        try:
            self.update_progress(0, "开始下载...")
            
            headers = self.get_headers()
            chapters = self.get_chapters_from_api(book_id, headers)
            if not chapters:
                raise Exception("未找到任何章节，请检查小说ID是否正确。")
            
            self.update_progress(10, "获取书籍信息...")
            name, author_name, description = self.get_book_info(book_id, headers)
            if not name:
                name = f"未知小说_{book_id}"
                author_name = "未知作者"
                description = "无简介"

            # 处理章节范围
            if start_chapter is not None and end_chapter is not None:
                chapters = chapters[start_chapter:end_chapter+1]
                self.log(f"选择下载章节 {start_chapter+1}-{end_chapter+1}")

            self.downloaded = self.load_status(save_path)
            todo_chapters = [ch for ch in chapters if ch["id"] not in self.downloaded]
            
            if not todo_chapters:
                self.update_progress(100, "所有章节已是最新，无需下载")
                return

            self.update_progress(20, f"开始下载：《{name}》, 总章节数: {len(chapters)}, 待下载: {len(todo_chapters)}")
            os.makedirs(save_path, exist_ok=True)
            
            output_file_path = os.path.join(save_path, f"{name}.{file_format}")
            if file_format == 'txt' and not os.path.exists(output_file_path):
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")

            success_count = 0
            failed_chapters = []
            lock = threading.Lock()

            # 批量下载模式
            if CONFIG["batch_config"]["enabled"] and CONFIG["batch_config"]["name"] == "qyuing":
                self.update_progress(30, "启用qyuing API批量下载模式...")
                batch_size = CONFIG["batch_config"]["max_batch_size"]
                
                total_batches = (len(todo_chapters) + batch_size - 1) // batch_size
                for i in range(0, len(todo_chapters), batch_size):
                    if self.is_cancelled:
                        return
                        
                    batch = todo_chapters[i:i + batch_size]
                    item_ids = [chap["id"] for chap in batch]
                    
                    current_batch = i // batch_size + 1
                    progress = 30 + (current_batch / total_batches) * 40  # 30%-70%
                    self.update_progress(progress, f"批量下载第 {current_batch}/{total_batches} 批")
                    
                    batch_results = self.batch_download_chapters(item_ids, headers)
                    if not batch_results:
                        self.log(f"第 {current_batch} 批下载失败")
                        failed_chapters.extend(batch)
                        continue
                    
                    for chap in batch:
                        content = batch_results.get(chap["id"], "")
                        if isinstance(content, dict):
                            content = content.get("content", "")
                        
                        if content:
                            processed = self.process_chapter_content(content)
                            with lock:
                                self.chapter_results[chap["index"]] = {
                                    "base_title": chap["title"],
                                    "api_title": "",
                                    "content": processed
                                }
                                self.downloaded.add(chap["id"])
                                success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chap)
                
                todo_chapters = failed_chapters.copy()
                failed_chapters = []
                self.write_downloaded_chapters_in_order(output_file_path, name, author_name, description, file_format)
                self.save_status(save_path, self.downloaded)

            # 单章下载模式
            if todo_chapters:
                self.update_progress(70, f"开始单章下载模式，剩余 {len(todo_chapters)} 个章节...")
                
                def download_task(chapter):
                    nonlocal success_count
                    if self.is_cancelled:
                        return
                        
                    try:
                        title, content = self.down_text(chapter["id"], headers, book_id)
                        if content:
                            with lock:
                                self.chapter_results[chapter["index"]] = {
                                    "base_title": chapter["title"],
                                    "api_title": title,
                                    "content": content
                                }
                                self.downloaded.add(chapter["id"])
                                success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chapter)
                    except Exception as e:
                        self.log(f"章节 {chapter['id']} 下载失败！")
                        with lock:
                            failed_chapters.append(chapter)

                attempt = 1
                while todo_chapters and not self.is_cancelled:
                    self.log(f"第 {attempt} 次尝试，剩余 {len(todo_chapters)} 个章节...")
                    attempt += 1
                    
                    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
                        futures = [executor.submit(download_task, ch) for ch in todo_chapters]
                        
                        completed = 0
                        for future in as_completed(futures):
                            if self.is_cancelled:
                                break
                            completed += 1
                            progress = 70 + (completed / len(todo_chapters)) * 25  # 70%-95%
                            self.update_progress(progress, f"单章下载进度: {completed}/{len(todo_chapters)}")
                    
                    self.write_downloaded_chapters_in_order(output_file_path, name, author_name, description, file_format)
                    self.save_status(save_path, self.downloaded)
                    todo_chapters = failed_chapters.copy()
                    failed_chapters = []
                    
                    if todo_chapters and not self.is_cancelled:
                        time.sleep(1)

            if not self.is_cancelled:
                self.update_progress(100, f"下载完成！成功下载 {success_count} 个章节")
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"下载失败: {error_msg}")
            if hasattr(self, 'downloaded'):
                self.write_downloaded_chapters_in_order(output_file_path, name, author_name, description, file_format)
                self.save_status(save_path, self.downloaded)
            raise

    def write_downloaded_chapters_in_order(self, output_file_path, name, author_name, description, file_format):
        """按章节顺序写入"""
        if not self.chapter_results:
            return
            
        if file_format == 'txt':
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")
                for idx in sorted(self.chapter_results.keys()):
                    result = self.chapter_results[idx]
                    title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                    f.write(f"{title}\n{result['content']}\n\n")
        elif file_format == 'epub':
            # 为EPUB生成一个临时的chapters列表
            temp_chapters = []
            for idx in sorted(self.chapter_results.keys()):
                temp_chapters.append({"index": idx})
            
            book = self.create_epub_book(name, author_name, description, self.chapter_results, temp_chapters)
            epub.write_epub(output_file_path, book, {})


# 为了兼容现有GUI，保持TomatoNovelAPI类的接口
class TomatoNovelAPI:
    def __init__(self):
        self.downloader = EnhancedNovelDownloader()
    
    def search_novels(self, keyword, offset=0, tab_type=1):
        """搜索小说 - 保持原有接口"""
        # 这里可以集成更多搜索功能，暂时返回示例
        return {
            "success": True,
            "data": {
                "items": [],
                "has_more": False,
                "next_offset": 0
            }
        }
    
    def get_novel_info(self, book_id):
        """获取小说信息 - 保持原有接口"""
        headers = self.downloader.get_headers()
        name, author, description = self.downloader.get_book_info(book_id, headers)
        
        if name:
            return {
                'isSuccess': True,
                'data': {
                    'data': {
                        'book_name': name,
                        'author': author,
                        'abstract': description,
                        'book_id': book_id
                    }
                }
            }
        return {'isSuccess': False, 'errorMsg': '获取书籍信息失败'}
    
    def get_book_details(self, book_id):
        """获取书籍详细信息（章节列表）"""
        headers = self.downloader.get_headers()
        chapters = self.downloader.get_chapters_from_api(book_id, headers)
        
        if chapters:
            all_item_ids = [ch["id"] for ch in chapters]
            return {
                "data": {
                    "allItemIds": all_item_ids
                },
                "isSuccess": True
            }
        return None
    
    def download_full_novel(self, book_id, item_ids, progress_callback=None):
        """下载整本小说"""
        if progress_callback:
            self.downloader.progress_callback = progress_callback
        
        # 这里需要根据item_ids确定章节范围
        # 暂时简化处理
        try:
            save_path = os.getcwd()  # 临时保存路径
            self.downloader.run_download(book_id, save_path, 'txt')
            
            # 读取结果
            headers = self.downloader.get_headers()
            name, _, _ = self.downloader.get_book_info(book_id, headers)
            file_path = os.path.join(save_path, f"{name or book_id}.txt")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 模拟章节结构
                chapters = []
                for idx, item_id in enumerate(item_ids if isinstance(item_ids, list) else item_ids.split(',')):
                    chapters.append({
                        'title': f'第{idx+1}章',
                        'content': content  # 简化处理
                    })
                
                return {
                    'isSuccess': True,
                    'data': {
                        'data': chapters
                    }
                }
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"下载失败: {str(e)}")
        
        return {'isSuccess': False, 'errorMsg': '下载失败'}


if __name__ == "__main__":
    # 测试代码
    downloader = EnhancedNovelDownloader()
    
    def progress_callback(progress, message):
        print(f"Progress: {progress}% - {message}")
    
    downloader.progress_callback = progress_callback
    
    # 示例用法
    # downloader.run_download("7143038691944959011", "./downloads", "txt") 