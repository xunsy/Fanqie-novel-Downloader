#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
番茄小说API调用脚本 - 增强版
完全集成参考.py的下载功能，支持GUI进度回调
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
import urllib.parse
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

def make_request(url, headers=None, params=None, data=None, method='GET', verify=False, timeout=None):
    """通用的请求函数"""
    if headers is None:
        headers = get_headers()
    
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
        print(f"请求失败: {str(e)}")
        raise

def get_headers() -> Dict[str, str]:
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

def fetch_api_endpoints_from_server():
    """从服务器获取API列表"""
    try:
        headers = get_headers()
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
            
            print("成功从服务器获取API列表!")
            return True
        else:
            print(f"获取API列表失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"获取API列表异常: {str(e)}")

def extract_chapters(soup):
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

def batch_download_chapters(item_ids, headers):
    """批量下载章节内容"""
    if not CONFIG["batch_config"]["enabled"] or CONFIG["batch_config"]["name"] != "qyuing":
        print("批量下载功能仅限qyuing API")
        return None
        
    batch_config = CONFIG["batch_config"]
    url = f"{batch_config['base_url']}{batch_config['batch_endpoint']}"
    
    try:
        batch_headers = headers.copy()
        if batch_config["token"]:
            batch_headers["token"] = batch_config["token"]
        batch_headers["Content-Type"] = "application/json"
        
        payload = {"item_ids": item_ids}
        response = make_request(
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
            print(f"批量下载失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"批量下载异常！")
        return None

def process_chapter_content(content):
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
        print(f"内容处理错误: {str(e)}")
        return str(content)

def down_text(chapter_id, headers, book_id=None):
    """下载章节内容"""
    content = ""
    chapter_title = ""
    first_error_printed = False

    if not hasattr(down_text, "api_status"):
        down_text.api_status = {endpoint["url"]: {
            "last_response_time": float('inf'),
            "error_count": 0,
            "last_try_time": 0
        } for endpoint in CONFIG["api_endpoints"]}

    # 记录未成功的id
    failed_chapter_id = chapter_id
    
    for idx, endpoint in enumerate(CONFIG["api_endpoints"]):
        current_endpoint = endpoint["url"]
        api_name = endpoint["name"]
        
        down_text.api_status[endpoint["url"]]["last_try_time"] = time.time()
        
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
                
                response = make_request(
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
                response = make_request(
                    current_endpoint, 
                    headers=headers.copy(),
                    timeout=CONFIG["request_timeout"],
                    verify=False
                )
            
            response_time = time.time() - start_time
            down_text.api_status[endpoint["url"]].update({
                "last_response_time": response_time,
                "error_count": max(0, down_text.api_status[endpoint["url"]]["error_count"] - 1)
            })
            
            data = response.json()
            
            if api_name == "fanqie_sdk":
                content = data.get("data", {}).get("content", "")
                chapter_title = data.get("data", {}).get("title", "")
                if content:
                    processed_content = process_chapter_content(content)
                    processed_content = re.sub(r'^(\s*)', r'    ', processed_content, flags=re.MULTILINE)
                    return chapter_title, processed_content
            elif api_name == "lsjk" and content:
                paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                formatted_content = '\n'.join('    ' + line if line.strip() else line 
                                            for line in cleaned_content.split('\n'))
                return chapter_title, formatted_content
            elif api_name == "qyuing" and data.get("code") == 0 and content:
                processed_content = process_chapter_content(content)
                return chapter_title, processed_content
            elif api_name == "fqweb":
                if data.get("data", {}).get("code") in ["0", 0]:
                    content = data.get("data", {}).get("data", {}).get("content", "")
                    if content:
                        processed_content = process_chapter_content(content)
                        processed_content = re.sub(r'^(\s*)', r'    ', processed_content, flags=re.MULTILINE)                        
                        return "", processed_content

            if not first_error_printed:
                print(f"API：{api_name}错误，无法下载章节，正在重试")
                first_error_printed = True
            down_text.api_status[endpoint["url"]]["error_count"] += 1
        except Exception as e:
            if not first_error_printed:
                print(f"API：{api_name}错误，无法下载章节，正在重试")
                first_error_printed = True
            down_text.api_status[endpoint["url"]]["error_count"] += 1
            time.sleep(3)
        
        if idx < len(CONFIG["api_endpoints"]) - 1:
            print("正在切换到下一个api")
    
    print(f"所有API尝试失败，无法下载章节 {chapter_id}")
    return None, None

def get_chapters_from_api(book_id, headers):
    """从API获取章节列表"""
    try:
        page_url = f'https://fanqienovel.com/page/{book_id}'
        response = requests.get(page_url, headers=headers, timeout=CONFIG["request_timeout"])
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        chapters = extract_chapters(soup)  
        
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
        print(f"获取章节列表失败: {str(e)}")
        return None

def get_book_info(book_id, headers):
    """获取书名、作者、简介"""
    url = f'https://fanqienovel.com/page/{book_id}'
    try:
        response = requests.get(url, headers=headers, timeout=CONFIG["request_timeout"])
        if response.status_code != 200:
            print(f"网络请求失败，状态码: {response.status_code}")
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
        print(f"获取书籍信息失败: {str(e)}")
        return None, None, None

def load_status(save_path):
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

def save_status(save_path, downloaded):
    """保存下载状态"""
    status_file = os.path.join(save_path, CONFIG["status_file"])
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(list(downloaded), f, ensure_ascii=False, indent=2)

class EnhancedNovelDownloader:
    """增强型小说下载器"""
    
    def __init__(self):
        self.progress_callback = None
        self.is_cancelled = False
        self.chapter_results = {}
        
    def cancel_download(self):
        """取消下载"""
        self.is_cancelled = True
        
    def run_download(self, book_id, save_path, file_format='txt', start_chapter=None, end_chapter=None):
        """运行下载"""
        try:
            # 初始化API端点
            if not CONFIG["api_endpoints"]:
                print("正在从服务器获取API列表...")
                fetch_api_endpoints_from_server()
            
            headers = get_headers()
            chapters = get_chapters_from_api(book_id, headers)
            if not chapters:
                raise Exception("未找到任何章节，请检查小说ID是否正确。")
            
            name, author_name, description = get_book_info(book_id, headers)
            if not name:
                name = f"未知小说_{book_id}"
                author_name = "未知作者"
                description = "无简介"

            # 确定下载范围
            if start_chapter is not None and end_chapter is not None:
                chapters = chapters[start_chapter:end_chapter+1]
                output_filename = f"{name}_第{start_chapter+1}-{end_chapter+1}章.{file_format}"
            else:
                output_filename = f"{name}.{file_format}"

            downloaded = load_status(save_path)
            todo_chapters = [ch for ch in chapters if ch["id"] not in downloaded]
            
            if self.progress_callback:
                self.progress_callback(5, f"开始下载：《{name}》, 总章节数: {len(chapters)}, 待下载: {len(todo_chapters)}")

            os.makedirs(save_path, exist_ok=True)
            output_file_path = os.path.join(save_path, output_filename)
            
            success_count = 0
            failed_chapters = []
            self.chapter_results = {}
            lock = threading.Lock()

            # 批量下载模式
            if CONFIG["batch_config"]["enabled"] and CONFIG["batch_config"]["name"] == "qyuing":
                if self.progress_callback:
                    self.progress_callback(10, "启用qyuing API批量下载模式...")
                    
                batch_size = CONFIG["batch_config"]["max_batch_size"]
                
                for i in range(0, len(todo_chapters), batch_size):
                    if self.is_cancelled:
                        break
                        
                    batch = todo_chapters[i:i + batch_size]
                    item_ids = [chap["id"] for chap in batch]
                    
                    if self.progress_callback:
                        progress = 10 + (i / len(todo_chapters)) * 60
                        self.progress_callback(progress, f"批量下载第 {i//batch_size + 1} 批...")
                    
                    batch_results = batch_download_chapters(item_ids, headers)
                    if not batch_results:
                        failed_chapters.extend(batch)
                        continue
                    
                    for chap in batch:
                        content = batch_results.get(chap["id"], "")
                        if isinstance(content, dict):
                            content = content.get("content", "")
                        
                        if content:
                            processed = process_chapter_content(content)
                            with lock:
                                self.chapter_results[chap["index"]] = {
                                    "base_title": chap["title"],
                                    "api_title": "",
                                    "content": processed
                                }
                                downloaded.add(chap["id"])
                                success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chap)
                
                todo_chapters = failed_chapters.copy()
                failed_chapters = []
                save_status(save_path, downloaded)

            # 单章下载模式（处理剩余章节）
            if todo_chapters and not self.is_cancelled:
                if self.progress_callback:
                    self.progress_callback(70, f"开始单章下载模式，剩余 {len(todo_chapters)} 个章节...")
                
                def download_task(chapter):
                    nonlocal success_count
                    try:
                        if self.is_cancelled:
                            return
                            
                        title, content = down_text(chapter["id"], headers, book_id)
                        if content:
                            with lock:
                                self.chapter_results[chapter["index"]] = {
                                    "base_title": chapter["title"],
                                    "api_title": title,
                                    "content": content
                                }
                                downloaded.add(chapter["id"])
                                success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chapter)
                    except Exception as e:
                        with lock:
                            failed_chapters.append(chapter)

                # 使用线程池下载
                with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
                    futures = [executor.submit(download_task, ch) for ch in todo_chapters]
                    
                    completed_count = 0
                    for future in as_completed(futures):
                        if self.is_cancelled:
                            break
                        completed_count += 1
                        if self.progress_callback:
                            progress = 70 + (completed_count / len(todo_chapters)) * 25
                            self.progress_callback(progress, f"单章下载进度: {completed_count}/{len(todo_chapters)}")
                
                save_status(save_path, downloaded)

            # 保存文件
            if not self.is_cancelled and self.chapter_results:
                if self.progress_callback:
                    self.progress_callback(95, "正在保存文件...")
                
                self._write_downloaded_chapters_in_order(output_file_path, name, author_name, description, file_format)
                
                if self.progress_callback:
                    self.progress_callback(100, f"下载完成！成功下载 {success_count} 个章节")

        except Exception as e:
            if self.progress_callback:
                self.progress_callback(-1, f"下载错误: {str(e)}")
            raise e

    def _write_downloaded_chapters_in_order(self, output_file_path, name, author_name, description, file_format):
        """按章节顺序写入文件，epub时自动传递封面url"""
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
            # 传递封面url（如有）
            thumb_url = None
            for idx in sorted(self.chapter_results.keys()):
                if 'thumb_url' in self.chapter_results[idx]:
                    thumb_url = self.chapter_results[idx]['thumb_url']
                    if thumb_url:
                        break
            self.epub_cover_url = thumb_url
            self._create_epub_book(output_file_path, name, author_name, description)
        # 下载完成后自动清理chapter.json
        try:
            status_file = os.path.join(os.path.dirname(output_file_path), CONFIG["status_file"])
            if os.path.exists(status_file):
                os.remove(status_file)
        except Exception as e:
            print(f"自动清理chapter.json失败: {e}")

    def _create_epub_book(self, output_file_path, name, author_name, description):
        """创建EPUB文件，插入详细信息页面和封面"""
        book = epub.EpubBook()
        book.set_identifier(f'book_{name}_{int(time.time())}')
        book.set_title(name)
        book.set_language('zh-CN')
        book.add_author(author_name)
        book.add_metadata('DC', 'description', description)

        # 详细信息页面
        info_html = f"""
        <html><head><title>书籍信息</title></head><body>
        <h1>{name}</h1>
        <p><b>作者：</b>{author_name}</p>
        <p><b>简介：</b>{description}</p>
        </body></html>
        """
        info_chapter = epub.EpubHtml(title='书籍信息', file_name='info.xhtml', lang='zh-CN')
        info_chapter.content = info_html
        book.add_item(info_chapter)

        book.toc = [info_chapter]
        spine = ['nav', info_chapter]

        for idx in sorted(self.chapter_results.keys()):
            result = self.chapter_results[idx]
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

        # 封面处理（如有thumb_url）
        # 取第一个章节的thumb_url（如有）
        thumb_url = None
        for idx in sorted(self.chapter_results.keys()):
            if 'thumb_url' in self.chapter_results[idx]:
                thumb_url = self.chapter_results[idx]['thumb_url']
                if thumb_url:
                    break
        if not thumb_url:
            # 兼容外部传入
            thumb_url = getattr(self, 'epub_cover_url', None)
        if thumb_url:
            try:
                import requests
                resp = requests.get(thumb_url, timeout=10)
                if resp.status_code == 200:
                    ext = 'jpg'
                    ct = resp.headers.get('content-type', '')
                    if 'png' in ct:
                        ext = 'png'
                    elif 'webp' in ct:
                        ext = 'webp'
                    book.set_cover(f"cover.{ext}", resp.content)
            except Exception as e:
                print(f"封面下载失败: {e}")

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        epub.write_epub(output_file_path, book, {})


class TomatoNovelAPI:
    """番茄小说API类 - 集成增强型下载器"""
    
    def __init__(self):
        """初始化API，集成增强型下载器"""
        # 初始化增强型下载器
        self.enhanced_downloader = EnhancedNovelDownloader()
        
        # 下载状态
        self.current_progress_callback = None
        
        # 初始化API端点
        if not CONFIG["api_endpoints"]:
            fetch_api_endpoints_from_server()
    
    def search_novels(self, keyword, offset=0, tab_type=1):
        """
        使用fqweb.jsj66.com的API进行搜索，适配真实返回结构，返回与原来兼容的数据结构。
        """
        try:
            url = "http://fqweb.jsj66.com/search"
            params = {
                "query": keyword,
                "page": offset // 10 + 1  # 页码从1开始
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            items = []
            # 适配真实结构
            if (
                data.get("data")
                and data["data"].get("code") in ("0", 0)
                and data["data"].get("search_tabs")
            ):
                for tab in data["data"]["search_tabs"]:
                    for entry in tab.get("data", []):
                        for book in entry.get("book_data", []):
                            items.append({
                                "book_id": book.get("book_id", book.get("id", "")),
                                "book_name": book.get("book_name", book.get("name", "")),
                                "author": book.get("author", "未知作者"),
                                "category": book.get("category", ""),
                                "abstract": book.get("abstract", book.get("desc", "")),
                                "score": book.get("score", ""),
                                "serial_count": book.get("serial_count", ""),
                                "word_number": book.get("word_number", ""),
                                "thumb_url": book.get("thumb_url", ""),
                                "creation_status": book.get("creation_status", ""),
                                "tags": book.get("tags", ""),
                                "sub_info": book.get("sub_info", ""),
                                "tomato_book_status": book.get("tomato_book_status", ""),
                                "source": "fqweb"
                            })
            return {
                "success": True,
                "data": {
                    "items": items,
                    "has_more": len(items) == 10,
                    "next_offset": offset + 10,
                    "search_keyword": keyword,
                    "source": "fqweb"
                }
            }
        except Exception as e:
            print(f"fqweb搜索失败: {e}")
        return {
            "success": False,
            "data": {
                "items": [],
                "has_more": False,
                "next_offset": offset + 10,
                "search_keyword": keyword,
                "source": "fqweb"
            }
        }

    def get_novel_info(self, book_id):
        """
        获取小说信息 - 使用参考.py中的方法
        
        Args:
            book_id (str): 小说ID
            
        Returns:
            dict: 小说信息
        """
        try:
            # 使用参考.py中的方法获取书籍信息
            headers = get_headers()
            name, author, description = get_book_info(book_id, headers)
            
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
        except Exception as e:
            print(f"获取书籍信息失败: {e}")
        
        # API失败
        print("获取书籍信息失败")
        return {'isSuccess': False, 'errorMsg': '获取书籍信息失败'}
    
    def get_chapter_content(self, item_ids):
        """
        获取章节内容 - 使用参考.py中的方法
        
        Args:
            item_ids (str): 章节ID
            
        Returns:
            dict: 章节内容
        """
        try:
            headers = get_headers()
            title, content = down_text(item_ids, headers)
            
            if content:
                processed_content = process_chapter_content(content)
                # 构造符合预期格式的返回结果
                processed_result = {
                    'isSuccess': True,
                    'data': {
                        'data': {
                            'content': processed_content,
                            'title': title,
                            'chapter_word_number': len(processed_content.replace(' ', '').replace('\n', '').replace('\t', ''))
                        }
                    }
                }
                return processed_result
        except Exception as e:
            print(f"获取章节内容失败: {e}")
            
        # API失败
        print("获取章节内容失败")
        return None
    
    def get_book_catalog(self, book_id):
        """
        获取书籍目录 - 使用参考.py中的方法
        
        Args:
            book_id (str): 书籍ID
            
        Returns:
            dict: 目录信息
        """
        try:
            headers = get_headers()
            chapters = get_chapters_from_api(book_id, headers)
            
            if chapters:
                # 构造符合预期格式的返回结果
                processed_result = {
                    'isSuccess': True,
                    'data': {
                        'data': {
                            'item_data_list': [{'item_id': ch['id']} for ch in chapters]
                        }
                    }
                }
                return processed_result
        except Exception as e:
            print(f"获取书籍目录失败: {e}")
            
        # API失败
        print("获取书籍目录失败")
        return None

    def get_book_details(self, bookId):
        """
        获取书籍详细信息（章节列表） - 使用参考.py中的方法
        
        Args:
            bookId (str): 书籍ID
            
        Returns:
            dict: 包含章节ID列表的书籍详细信息
        """
        try:
            # 使用参考.py中的方法获取章节列表
            headers = get_headers()
            chapters = get_chapters_from_api(bookId, headers)
            
            if chapters:
                all_item_ids = [ch["id"] for ch in chapters]
                print(f"使用参考.py方法获取到 {len(all_item_ids)} 个章节")
                return {
                    "data": {
                        "allItemIds": all_item_ids
                    },
                    "isSuccess": True
                }
        except Exception as e:
            print(f"获取章节列表失败: {e}")
        
        # API失败
        print("获取书籍详细信息失败")
        return None

    def download_full_novel(self, book_id, item_ids):
        """
        一次性下载整本小说 - 使用增强型下载器
        
        Args:
            book_id (str): 小说ID
            item_ids (list or str): 章节ID列表或逗号分隔的章节ID字符串
            
        Returns:
            dict: 小说完整内容
        """
        import tempfile
        
        # 设置进度回调
        self.enhanced_downloader.progress_callback = self.current_progress_callback
        
        try:
            # 创建临时目录用于下载
            with tempfile.TemporaryDirectory() as temp_dir:
                # 确定章节范围
                if isinstance(item_ids, list):
                    item_ids_list = item_ids
                else:
                    item_ids_list = item_ids.split(',') if isinstance(item_ids, str) else []
                
                if not item_ids_list:
                    return {
                        'isSuccess': False,
                        'errorMsg': '章节ID列表为空'
                    }
                
                # 获取完整章节列表以确定范围
                headers = get_headers()
                all_chapters = get_chapters_from_api(book_id, headers)
                
                if not all_chapters:
                    return {
                        'isSuccess': False,
                        'errorMsg': '无法获取章节列表'
                    }
                
                # 找到要下载的章节在全部章节中的位置
                chapter_indices = []
                for item_id in item_ids_list:
                    for i, chapter in enumerate(all_chapters):
                        if chapter['id'] == item_id:
                            chapter_indices.append(i)
                            break
                
                if not chapter_indices:
                    return {
                        'isSuccess': False,
                        'errorMsg': '未找到匹配的章节'
                    }
                
                start_chapter = min(chapter_indices)
                end_chapter = max(chapter_indices)
                
                # 使用增强型下载器下载
                self.enhanced_downloader.run_download(
                    book_id, 
                    temp_dir, 
                    'txt',
                    start_chapter,
                    end_chapter
                )
                
                # 构建章节内容列表
                chapters_content = []
                for idx in range(start_chapter, end_chapter + 1):
                    if idx in self.enhanced_downloader.chapter_results:
                        result = self.enhanced_downloader.chapter_results[idx]
                        chapters_content.append({
                            'title': result['base_title'],
                            'content': result['content']
                        })
                
                return {
                    'isSuccess': True,
                    'data': {
                        'data': chapters_content,
                        'totalChapters': len(item_ids_list),
                        'successChapters': len(chapters_content),
                        'failedChapters': len(item_ids_list) - len(chapters_content)
                    }
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"增强型下载器错误: {error_msg}")
            
            return {
                'isSuccess': False,
                'errorMsg': f'下载失败: {error_msg}'
            }
    
    def set_progress_callback(self, callback: Optional[Callable] = None):
        """设置进度回调函数"""
        self.current_progress_callback = callback
        if self.enhanced_downloader:
            self.enhanced_downloader.progress_callback = callback
    
    def cancel_download(self):
        """取消当前下载"""
        if self.enhanced_downloader:
            self.enhanced_downloader.cancel_download()


def main():
    """主函数，用于独立运行脚本"""
    api = TomatoNovelAPI()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  搜索小说: python tomato_novel_api.py search <关键词>")
        print("  获取小说信息: python tomato_novel_api.py novel_info <书籍ID>")
        print("  获取书籍详细信息: python tomato_novel_api.py book_details <书籍ID>")
        print("  获取书籍目录: python tomato_novel_api.py catalog <书籍ID>")
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
            
    elif command == "catalog":
        if len(sys.argv) < 3:
            print("请提供书籍ID")
            return
        
        book_id = sys.argv[2]
        print(f"正在获取书籍目录: {book_id}")
        result = api.get_book_catalog(book_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("获取书籍目录失败")
            
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