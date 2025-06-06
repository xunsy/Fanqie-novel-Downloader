#!/usr/bin/env python3
"""
番茄小说下载器核心模块
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
import stem
from stem import Signal
from stem.control import Controller
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from collections import OrderedDict
from fake_useragent import UserAgent
from typing import Optional, Dict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import gzip
from urllib.parse import urlencode

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# 添加Tor配置
TOR_CONFIG = {
    "enabled": False,
    "proxy_port": 9050,
    "max_retries": 3,
    "change_ip_after": 980,
    "request_timeout": 35
}

# 初始化请求计数器
request_counter = 0

def get_tor_session():
    """创建新的Tor会话"""
    session = requests.session()
    session.proxies = {
        'http': f'socks5h://127.0.0.1:{TOR_CONFIG["proxy_port"]}',
        'https': f'socks5h://127.0.0.1:{TOR_CONFIG["proxy_port"]}'
    }
    return session

def renew_tor_ip():
    """重建会话"""
    if not TOR_CONFIG["enabled"]:
        return

    print("正在重建Tor会话更换IP...")
    global request_counter
    request_counter = 0
    time.sleep(5)
    print("IP更换完成")

def check_tor_connection():
    """检查Tor连接是否正常"""
    try:
        session = get_tor_session()
        response = session.get(
            "https://check.torproject.org/",
            timeout=TOR_CONFIG["request_timeout"]
        )
        if "Congratulations" in response.text:
            print("Tor连接成功!")
            return True
    except Exception as e:
        print(f"Tor连接检查失败: {str(e)}")
    return False

def enable_tor_support():
    """启用Tor支持"""
    TOR_CONFIG["enabled"] = True
    print("正在启用Tor支持...")
    if check_tor_connection():
        print("Tor支持已启用!")
        return True
    else:
        print("无法连接到Tor网络，请确保Tor服务正在运行，将使用其他下载渠道进行下载\n")
        TOR_CONFIG["enabled"] = False
        return False

def make_request(url, headers=None, params=None, data=None, method='GET', verify=False, use_tor=False, timeout=None):
    """通用的请求函数"""
    global request_counter

    if headers is None:
        headers = get_headers()

    session = None
    if use_tor and TOR_CONFIG["enabled"]:
        session = get_tor_session()
        # 计数器逻辑
        request_counter += 1
        if request_counter % TOR_CONFIG["change_ip_after"] == 0:
            renew_tor_ip()
    else:
        session = requests.Session()

    try:
        request_params = {
            'headers': headers,
            'params': params,
            'verify': verify,
            'timeout': timeout if timeout is not None else TOR_CONFIG["request_timeout"]
        }

        if data:
            request_params['data'] = data

        if method.upper() == 'GET':
            response = session.get(url, **request_params)
        elif method.upper() == 'POST':
            response = session.post(url, **request_params)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        return response
    except Exception as e:
        print(f"请求失败: {str(e)}")
        if use_tor and TOR_CONFIG["enabled"]:
            renew_tor_ip()
            return make_request(url, headers, params, data, method, verify, use_tor, timeout)
        raise

# 全局配置
CONFIG = {
    "max_workers": 4,
    "max_retries": 3,
    "request_timeout": 15,
    "status_file": "chapter.json",
    "request_rate_limit": 0.4,
    "auth_token": "wcnmd91jb",
    "server_url": "http://74.113.96.176:5001/api/sources",
    "api_endpoints": [],
    "batch_config": {
        "name": "qyuing",
        "base_url": None,
        "batch_endpoint": None,
        "token": None,
        "max_batch_size": 290,
        "timeout": 10,
        "enabled": False
    }
}

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
                    # 添加到API端点列表
                    CONFIG["api_endpoints"].append({
                        "url": source["single_url"],
                        "name": source["name"]
                    })

                    # 检查是否支持批量下载
                    if source["name"] == CONFIG["batch_config"]["name"]:
                        base_url = source["single_url"].split('?')[0]
                        batch_endpoint = base_url.split('/')[-1]
                        base_url = base_url.rsplit('/', 1)[0] if '/' in base_url else base_url

                        # 配置批量下载
                        CONFIG["batch_config"]["base_url"] = base_url
                        CONFIG["batch_config"]["batch_endpoint"] = f"/{batch_endpoint}"
                        CONFIG["batch_config"]["token"] = source.get("token", "")
                        CONFIG["batch_config"]["enabled"] = True

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

        # 特殊章节
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
    if not CONFIG["batch_config"]["enabled"]:
        print("批量下载功能未启用")
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
            verify=False,
            use_tor=True
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
        # 移除HTML标签
        content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
        content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
        content = re.sub(r'</?article>', '', content)
        content = re.sub(r'<p[^>]*>', '\n    ', content)
        content = re.sub(r'</p>', '', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\\u003c|\\u003e', '', content)

        # 格式化段落
        content = re.sub(r'\n{3,}', '\n\n', content).strip()
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join(['    ' + line for line in lines])
    except Exception as e:
        print(f"内容处理错误: {str(e)}")
        return str(content)

def down_text(chapter_id, headers, book_id=None):
    """下载章节内容"""
    content = ""
    chapter_title = ""

    # 初始化API端点状态
    if not hasattr(down_text, "api_status"):
        down_text.api_status = {endpoint["url"]: {
            "last_response_time": float('inf'),
            "error_count": 0,
            "last_try_time": 0
        } for endpoint in CONFIG["api_endpoints"]}

    # 顺序尝试API
    for endpoint in CONFIG["api_endpoints"]:
        current_endpoint = endpoint["url"].format(chapter_id=chapter_id)
        api_name = endpoint["name"]

        down_text.api_status[endpoint["url"]]["last_try_time"] = time.time()

        try:
            # 随机延迟
            time.sleep(random.uniform(0.1, 0.5))

            start_time = time.time()
            response = make_request(
                current_endpoint,
                headers=headers.copy(),
                timeout=CONFIG["request_timeout"],
                verify=False,
                use_tor=True
            )

            response_time = time.time() - start_time
            down_text.api_status[endpoint["url"]].update({
                "last_response_time": response_time,
                "error_count": max(0, down_text.api_status[endpoint["name"]]["error_count"] - 1)
            })

            data = response.json()
            content = data.get("data", {}).get("content", "")
            chapter_title = data.get("data", {}).get("title", "")

            if api_name == "fqphp" and content:
                # 处理内容
                if len(content) > 20:
                    content = content[:-20]

                processed_content = process_chapter_content(content)
                return chapter_title, processed_content

            elif api_name == "lsjk" and content:
                # 处理内容
                paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                formatted_content = '\n'.join('    ' + line if line.strip() else line
                                            for line in cleaned_content.split('\n'))
                return chapter_title, formatted_content

            elif api_name == "qyuing" and data.get("code") == 0 and content:
                processed_content = process_chapter_content(content)
                return chapter_title, processed_content

            print(f"API返回空内容，继续尝试下一个API...")
            down_text.api_status[endpoint["name"]]["error_count"] += 1

        except Exception as e:
            print(f"API请求失败！")
            down_text.api_status[endpoint["name"]]["error_count"] += 1
            time.sleep(3)

    print(f"所有API尝试失败，无法下载章节 {chapter_id}")
    return None, None

def get_chapters_from_api(book_id, headers):
    """从API获取章节列表"""
    try:
        # 获取章节列表
        page_url = f'https://fanqienovel.com/page/{book_id}'
        response = requests.get(page_url, headers=headers, timeout=CONFIG["request_timeout"])
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        chapters = extract_chapters(soup)

        # 获取章节ID顺序
        api_url = f"https://fanqienovel.com/api/reader/directory/detail?bookId={book_id}"
        api_response = requests.get(api_url, headers=headers, timeout=CONFIG["request_timeout"])
        api_data = api_response.json()
        chapter_ids = api_data.get("data", {}).get("allItemIds", [])

        # 合并数据
        final_chapters = []
        for idx, chapter_id in enumerate(chapter_ids):
            # 查找网页解析的对应章节
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

        # 获取书名
        name_element = soup.find('h1')
        name = name_element.text if name_element else "未知书名"

        # 获取作者
        author_name = "未知作者"
        author_name_element = soup.find('div', class_='author-name')
        if author_name_element:
            author_name_span = author_name_element.find('span', class_='author-name-text')
            if author_name_span:
                author_name = author_name_span.text

        # 获取简介
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

def test_cloudflare_proxy():
    """测试Cloudflare Workers代理连接"""
    try:
        # 这里可以添加实际的代理测试逻辑
        # 目前返回True表示测试通过
        print("Cloudflare Workers代理测试通过")
        return True
    except Exception as e:
        print(f"Cloudflare Workers代理测试失败: {str(e)}")
        return False

def download_chapter(chapter, headers, save_path, book_name, downloaded, book_id):
    """下载单个章节"""
    if chapter["id"] in downloaded:
        return None

    # 获取内容
    _, content = down_text(chapter["id"], headers, book_id)

    if content:
        output_file_path = os.path.join(save_path, f"{book_name}.txt")
        try:
            with open(output_file_path, 'a', encoding='utf-8') as f:
                f.write(f'{chapter["title"]}\n')
                f.write(content + '\n\n')

            downloaded.add(chapter["id"])
            save_status(save_path, downloaded)
            return chapter["index"], content
        except Exception as e:
            print(f"写入文件失败: {str(e)}")
    return None

def Run(book_id, save_path):
    """运行下载"""
    def signal_handler(sig, frame):
        print("\n检测到程序中断，正在保存已下载内容...")
        write_downloaded_chapters_in_order()
        save_status(save_path, downloaded)
        print(f"已保存 {len(downloaded)} 个章节的进度")
        sys.exit(0)

    def write_downloaded_chapters_in_order():
        """按章节顺序写入"""
        if not chapter_results:
            return

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")
            for idx in range(len(chapters)):
                if idx in chapter_results:
                    result = chapter_results[idx]
                    title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                    f.write(f"{title}\n{result['content']}\n\n")

    # 信号处理
    signal.signal(signal.SIGINT, signal_handler)

    try:
        headers = get_headers()
        chapters = get_chapters_from_api(book_id, headers)
        if not chapters:
            print("未找到任何章节，请检查小说ID是否正确。")
            return

        name, author_name, description = get_book_info(book_id, headers)
        if not name:
            name = f"未知小说_{book_id}"
            author_name = "未知作者"
            description = "无简介"

        downloaded = load_status(save_path)
        if downloaded:
            print(f"检测到您曾经下载过小说《{name}》。")
            if input("是否需要再次下载？(y/n)：") != "y":
                print("已取消下载")
                return

        todo_chapters = [ch for ch in chapters if ch["id"] not in downloaded]
        if not todo_chapters:
            print("所有章节已是最新，无需下载")
            return

        print(f"开始下载：《{name}》, 总章节数: {len(chapters)}, 待下载: {len(todo_chapters)}")
        os.makedirs(save_path, exist_ok=True)

        output_file_path = os.path.join(save_path, f"{name}.txt")
        if not os.path.exists(output_file_path):
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")

        success_count = 0
        failed_chapters = []
        chapter_results = {}
        lock = threading.Lock()

        # 批量下载
        if (len(todo_chapters) > 100 and
            CONFIG["batch_config"]["enabled"] and
            any(ep["name"] == "qyuing" for ep in CONFIG["api_endpoints"])):
            print("检测到大量章节，启用批量下载模式...")
            batch_size = CONFIG["batch_config"]["max_batch_size"]

            with tqdm(total=len(todo_chapters), desc="批量下载进度") as pbar:
                for i in range(0, len(todo_chapters), batch_size):
                    batch = todo_chapters[i:i + batch_size]
                    item_ids = [chap["id"] for chap in batch]

                    batch_results = batch_download_chapters(item_ids, headers)
                    if not batch_results:
                        print(f"第 {i//batch_size + 1} 批下载失败")
                        failed_chapters.extend(batch)
                        pbar.update(len(batch))
                        continue

                    # 处理并写入内容
                    for chap in batch:
                        # 从结果中获取内容
                        content = batch_results.get(chap["id"], "")
                        if isinstance(content, dict):
                            content = content.get("content", "")

                        if content:
                            processed = process_chapter_content(content)
                            with lock:
                                chapter_results[chap["index"]] = {
                                    "base_title": chap["title"],
                                    "api_title": "",
                                    "content": processed
                                }
                                downloaded.add(chap["id"])
                                success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chap)
                        pbar.update(1)

            todo_chapters = failed_chapters.copy()
            failed_chapters = []
            write_downloaded_chapters_in_order()
            save_status(save_path, downloaded)

        # 单章下载
        def download_task(chapter):
            nonlocal success_count
            try:
                title, content = down_text(chapter["id"], headers, book_id)
                if content:
                    with lock:
                        chapter_results[chapter["index"]] = {
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
                print(f"章节 {chapter['id']} 下载失败: {str(e)}")
                with lock:
                    failed_chapters.append(chapter)

        attempt = 1
        while todo_chapters:
            print(f"\n第 {attempt} 次尝试，剩余 {len(todo_chapters)} 个章节...")
            attempt += 1

            with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
                futures = [executor.submit(download_task, ch) for ch in todo_chapters]

                with tqdm(total=len(todo_chapters), desc="单章下载进度") as pbar:
                    for _ in as_completed(futures):
                        pbar.update(1)

            write_downloaded_chapters_in_order()
            save_status(save_path, downloaded)
            todo_chapters = failed_chapters.copy()
            failed_chapters = []

            if todo_chapters:
                time.sleep(1)

        print(f"下载完成！成功下载 {success_count} 个章节")

    except Exception as e:
        print(f"运行错误: {str(e)}")
        if 'downloaded' in locals():
            write_downloaded_chapters_in_order()
            save_status(save_path, downloaded)

# GUI下载器类，用于兼容现有的GUI代码
class GUIdownloader:
    """GUI下载器类，用于在GUI环境中下载小说"""

    def __init__(self, book_id: str, save_path: str, status_callback: callable, progress_callback: callable):
        self.book_id = book_id
        self.save_path = save_path
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.stop_flag = False
        self.start_time = time.time()

    def stop_download(self):
        """停止下载"""
        self.stop_flag = True
        if self.status_callback:
            self.status_callback("下载已停止")

    def run(self):
        """运行下载"""
        try:
            if self.status_callback:
                self.status_callback("正在初始化...")

            # 从服务器获取API列表
            fetch_api_endpoints_from_server()

            if self.status_callback:
                self.status_callback("正在获取小说信息...")

            headers = get_headers()
            chapters = get_chapters_from_api(self.book_id, headers)
            if not chapters:
                if self.status_callback:
                    self.status_callback("未找到任何章节，请检查小说ID是否正确")
                return

            name, author_name, description = get_book_info(self.book_id, headers)
            if not name:
                name = f"未知小说_{self.book_id}"
                author_name = "未知作者"
                description = "无简介"

            if self.status_callback:
                self.status_callback(f"开始下载：《{name}》")

            downloaded = load_status(self.save_path)
            todo_chapters = [ch for ch in chapters if ch["id"] not in downloaded]

            # 计算总章节数和已下载章节数
            total_chapters = len(chapters)
            already_downloaded = len(downloaded)

            # 设置初始进度（基于已下载的章节）
            initial_progress = int(already_downloaded / total_chapters * 100) if total_chapters > 0 else 0
            if self.progress_callback:
                self.progress_callback(initial_progress)

            if not todo_chapters:
                if self.status_callback:
                    self.status_callback("所有章节已是最新，无需下载")
                if self.progress_callback:
                    self.progress_callback(100)
                return

            os.makedirs(self.save_path, exist_ok=True)

            output_file_path = os.path.join(self.save_path, f"{name}.txt")
            if not os.path.exists(output_file_path):
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")

            success_count = 0

            for i, chapter in enumerate(todo_chapters):
                if self.stop_flag:
                    break

                if self.status_callback:
                    self.status_callback(f"正在下载: {chapter['title']} ({already_downloaded + i + 1}/{total_chapters})")

                title, content = down_text(chapter["id"], headers, self.book_id)
                if content:
                    with open(output_file_path, 'a', encoding='utf-8') as f:
                        display_title = f'{chapter["title"]} {title}' if title else chapter["title"]
                        f.write(f"{display_title}\n{content}\n\n")

                    downloaded.add(chapter["id"])
                    save_status(self.save_path, downloaded)
                    success_count += 1

                # 更新进度（基于总章节数）
                current_downloaded = already_downloaded + i + 1
                progress = int(current_downloaded / total_chapters * 100)
                if self.progress_callback:
                    self.progress_callback(progress)

                time.sleep(CONFIG["request_rate_limit"])

            if self.status_callback:
                self.status_callback(f"下载完成！成功下载 {success_count} 个章节")

            if self.progress_callback:
                self.progress_callback(100)

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"下载过程中发生错误: {str(e)}")

def main():
    print("""欢迎使用番茄小说下载器精简版！
开发者：Dlmily
当前版本：v1.7
Github：https://github.com/Dlmily/Tomato-Novel-Downloader-Lite
赞助/了解新产品：https://afdian.com/a/dlbaokanluntanos
*使用前须知*：
    1.开始下载之后，您可能会过于着急而查看下载文件的位置，这是徒劳的，请耐心等待小说下载完成再查看！另外如果你要下载之前已经下载过的小说(在此之前已经删除了原txt文件)，那么你有可能会遇到"所有章节已是最新，无需下载"的情况，这时就请删除掉chapter.json，然后再次运行程序。
    2.您可以自行选择使用Tor网络进行下载，Tor网络能够很好地防止Api开发者封ip。

另：如果有带番茄svip的cookie或api，按照您的意愿投到"Issues"页中。
------------------------------------------""")
    use_tor = input("是否要使用Tor网络进行下载？(y/n, 默认为n): ").strip().lower()
    if use_tor == 'y':
        if not enable_tor_support():
            print("将不使用Tor网络继续运行")

    print("正在从服务器获取API列表...")
    fetch_api_endpoints_from_server()

    while True:
        book_id = input("请输入小说ID（输入q退出）：").strip()
        if book_id.lower() == 'q':
            break

        save_path = input("保存路径（留空为当前目录）：").strip() or os.getcwd()

        try:
            Run(book_id, save_path)
        except Exception as e:
            print(f"运行错误: {str(e)}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
