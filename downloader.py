#!/usr/bin/env python3
"""
番茄小说下载器核心模块
合并了原core/fq_downloader.py和core/request_handler.py的功能
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from collections import OrderedDict
from fake_useragent import UserAgent
from typing import Optional, Dict, List, Any, Tuple, Set
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import gzip
from urllib.parse import urlencode, quote

# 导入全局配置
try:
    from config import CONFIG
except ImportError:
    # 如果无法导入配置，使用默认配置
    CONFIG = {
        "tor": {
            "enabled": False,
            "proxy_port": 9050,
            "max_retries": 3,
            "change_ip_after": 980,
            "request_timeout": 35
        }
    }

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if hasattr(requests, 'packages'):
    requests.packages.urllib3.disable_warnings()

# 全局变量
request_counter = 0

def get_tor_session():
    """创建新的Tor会话"""
    session = requests.session()
    tor_config = CONFIG.get("tor", {})
    proxy_port = tor_config.get("proxy_port", 9050)
    session.proxies = {
        'http': f'socks5h://127.0.0.1:{proxy_port}',
        'https': f'socks5h://127.0.0.1:{proxy_port}'
    }
    return session

def renew_tor_ip():
    tor_config = CONFIG.get("tor", {})
    if not tor_config.get("enabled", False):
        return

    print("正在重建Tor会话更换IP...")
    global request_counter
    request_counter = 0
    time.sleep(5)
    print("IP更换完成")

def check_tor_connection():
    try:
        session = get_tor_session()
        tor_config = CONFIG.get("tor", {})
        timeout = tor_config.get("request_timeout", 35)
        response = session.get("https://check.torproject.org/", timeout=timeout)
        return "Congratulations" in response.text
    except Exception:
        return False

def enable_tor_support():
    """启用Tor支持"""
    CONFIG["tor"]["enabled"] = True
    if check_tor_connection():
        return True
    CONFIG["tor"]["enabled"] = False
    return False

def disable_tor_support():
    """禁用Tor支持"""
    CONFIG["tor"]["enabled"] = False

def make_request(url: str, headers: Dict[str, str] = None, timeout: int = 15, verify: bool = False, use_tor: bool = None, **kwargs) -> requests.Response:
    """
    统一的请求函数，支持Tor代理

    Args:
        url: 请求URL
        headers: 请求头
        timeout: 超时时间
        verify: 是否验证SSL证书
        use_tor: 是否使用Tor代理，None时根据全局配置决定
        **kwargs: 其他requests参数

    Returns:
        requests.Response对象
    """
    if headers is None:
        headers = {}

    # 决定是否使用Tor
    tor_config = CONFIG.get("tor", {})
    should_use_tor = use_tor if use_tor is not None else tor_config.get("enabled", False)

    if should_use_tor:
        # 使用Tor代理
        session = get_tor_session()
        response = session.get(url, headers=headers, timeout=timeout, verify=verify, **kwargs)

        # 更新请求计数器
        global request_counter
        request_counter += 1

        # 检查是否需要更换IP
        change_ip_after = tor_config.get("change_ip_after", 980)
        if request_counter >= change_ip_after:
            renew_tor_ip()

        return response
    else:
        # 普通请求
        return requests.get(url, headers=headers, timeout=timeout, verify=verify, **kwargs)

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

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不合法字符"""
    if not filename:
        return ""

    # 移除或替换不合法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, '_', filename)

    # 移除前后空格和点
    filename = filename.strip(' .')

    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]

    return filename

def _log_or_print(logger_callback: Optional[callable], message: str):
    """统一的日志输出函数"""
    if logger_callback:
        logger_callback(message)
    else:
        print(message)

def apply_cloudflare_proxy(url: str) -> str:
    """
    应用Cloudflare Workers反代

    Args:
        url: 原始URL

    Returns:
        处理后的URL（如果启用反代则返回反代URL，否则返回原URL）
    """
    proxy_config = CONFIG.get("cloudflare_proxy", {})

    if not proxy_config.get("enabled", False):
        return url

    proxy_domain = proxy_config.get("proxy_domain", "").strip()
    if not proxy_domain:
        return url

    # 确保proxy_domain格式正确
    if not proxy_domain.startswith(('http://', 'https://')):
        proxy_domain = f"https://{proxy_domain}"

    # 移除末尾的斜杠
    proxy_domain = proxy_domain.rstrip('/')

    # 提取原URL的路径和查询参数
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)

    # 构建反代URL：proxy_domain + 原URL的路径和查询参数
    proxy_url = f"{proxy_domain}{parsed.path}"
    if parsed.query:
        proxy_url += f"?{parsed.query}"

    return proxy_url

def test_cloudflare_proxy() -> bool:
    """
    测试Cloudflare Workers反代连接

    Returns:
        bool: 连接是否成功
    """
    proxy_config = CONFIG.get("cloudflare_proxy", {})

    if not proxy_config.get("enabled", False):
        return False

    proxy_domain = proxy_config.get("proxy_domain", "").strip()
    if not proxy_domain:
        return False

    # 确保proxy_domain格式正确
    if not proxy_domain.startswith(('http://', 'https://')):
        proxy_domain = f"https://{proxy_domain}"

    # 移除末尾的斜杠
    proxy_domain = proxy_domain.rstrip('/')

    # 构建测试URL
    test_endpoint = proxy_config.get("test_endpoint", "/test")
    test_url = f"{proxy_domain}{test_endpoint}"

    try:
        response = make_request(test_url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# 下载器配置
DOWNLOADER_CONFIG = {
    "backup_api_endpoints": [
        "https://fqphp.gxom.cn/content?item_id={chapter_id}",
        "https://api.cenguigui.cn/api/tomato/content.php?item_id={chapter_id}",
        "https://lsjk.zyii.xyz:3666/content?item_id={chapter_id}",
        "http://nu1.jingluo.love/content?item_id={chapter_id}",
        "http://nu2.jingluo.love/content?item_id={chapter_id}"
    ],
    "api_keys": {
        "fqphp.gxom.cn": "BkmpOhGYbhFv"
    },
    "request_timeout": 15
}

# Variable to store last request time for rate limiting official API
_official_api_last_request_time = [0.0]

def down_text(chapter_id: str, book_id: Optional[str] = None, logger_callback: Optional[callable] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Downloads chapter content. Tries official API first, then backups.
    Returns (chapter_title, cleaned_content) or (None, None) on failure.
    """
    log_func = lambda msg: _log_or_print(logger_callback, msg)

    # 初始化API端点状态
    if not hasattr(down_text, "api_status"):
        down_text.api_status = {endpoint: {
            "last_response_time": float('inf'),
            "error_count": 0,
            "last_try_time": 0
        } for endpoint in DOWNLOADER_CONFIG["backup_api_endpoints"]}

    # 顺序尝试API
    for api_endpoint_template in DOWNLOADER_CONFIG["backup_api_endpoints"]:
        current_endpoint = api_endpoint_template.format(chapter_id=chapter_id)
        down_text.api_status[api_endpoint_template]["last_try_time"] = time.time()

        try:
            # 随机延迟
            time.sleep(random.uniform(0.1, 0.5))

            # 添加密钥参数
            if "fqphp.gxom.cn" in api_endpoint_template:
                separator = "&" if "?" in current_endpoint else "?"
                current_endpoint += f"{separator}key={DOWNLOADER_CONFIG['api_keys']['fqphp.gxom.cn']}"

            # 应用Cloudflare Workers反代
            proxy_endpoint = apply_cloudflare_proxy(current_endpoint)

            start_time = time.time()
            response = make_request(
                proxy_endpoint,
                headers=get_headers(),
                timeout=DOWNLOADER_CONFIG["request_timeout"],
                verify=False,
                use_tor=True
            )

            response_time = time.time() - start_time
            down_text.api_status[api_endpoint_template].update({
                "last_response_time": response_time,
                "error_count": max(0, down_text.api_status[api_endpoint_template]["error_count"] - 1)
            })

            data = response.json()
            content = data.get("data", {}).get("content", "")
            chapter_title = data.get("data", {}).get("title", "")

            if "fqphp.gxom.cn" in api_endpoint_template and content:
                # 处理内容
                if len(content) > 20:
                    content = content[:-20]

                content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
                content = re.sub(r'</?article>', '', content)
                content = re.sub(r'<p[^>]*>', '\n    ', content)
                content = re.sub(r'</p>', '', content)
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\\u003c|\\u003e', '', content)

                content = re.sub(r'\n{3,}', '\n\n', content).strip()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                formatted_content = '\n'.join(['    ' + line for line in lines])
                return chapter_title, formatted_content

            elif "api.cenguigui.cn" in api_endpoint_template and data.get("code") == 200 and content:
                # 处理内容
                content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
                content = re.sub(r'</?article>', '', content)
                content = re.sub(r'<p idx="\d+">', '\n', content)
                content = re.sub(r'</p>', '\n', content)
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\\u003c|\\u003e', '', content)

                if chapter_title and content.startswith(chapter_title):
                    content = content[len(chapter_title):].lstrip()

                content = re.sub(r'\n{2,}', '\n', content).strip()
                formatted_content = '\n'.join(['    ' + line if line.strip() else line for line in content.split('\n')])
                return chapter_title, formatted_content

            elif "lsjk.zyii.xyz" in api_endpoint_template and content:
                # 处理内容
                paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                formatted_content = '\n'.join('    ' + line if line.strip() else line
                                            for line in cleaned_content.split('\n'))
                return chapter_title, formatted_content

            elif "jingluo.love" in api_endpoint_template and content:
                # 处理内容
                content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                content = re.sub(r'</?article>', '', content)
                content = re.sub(r'<p idx="\d+">', '\n', content)
                content = re.sub(r'</p>', '\n', content)
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\\u003c|\\u003e', '', content)

                if chapter_title and content.startswith(chapter_title):
                    content = content[len(chapter_title):].lstrip()

                content = re.sub(r'\n{2,}', '\n', content).strip()
                formatted_content = '\n'.join(['    ' + line if line.strip() else line for line in content.split('\n')])
                return chapter_title, formatted_content

            log_func(f"API端点 {api_endpoint_template} 返回空内容，继续尝试下一个API...")
            down_text.api_status[api_endpoint_template]["error_count"] += 1

        except Exception as e:
            log_func(f"API端点 {api_endpoint_template} 请求失败: {str(e)}")

            # 如果启用了反代且失败，尝试使用原始URL
            proxy_config = CONFIG.get("cloudflare_proxy", {})
            if (proxy_config.get("enabled", False) and
                proxy_config.get("fallback_to_original", True) and
                proxy_endpoint != current_endpoint):

                log_func(f"反代请求失败，尝试使用原始URL: {current_endpoint}")
                try:
                    start_time = time.time()
                    response = make_request(
                        current_endpoint,
                        headers=get_headers(),
                        timeout=DOWNLOADER_CONFIG["request_timeout"],
                        verify=False,
                        use_tor=True
                    )

                    response_time = time.time() - start_time
                    down_text.api_status[api_endpoint_template].update({
                        "last_response_time": response_time,
                        "error_count": max(0, down_text.api_status[api_endpoint_template]["error_count"] - 1)
                    })

                    data = response.json()
                    content = data.get("data", {}).get("content", "")
                    chapter_title = data.get("data", {}).get("title", "")

                    # 处理内容的逻辑与上面相同
                    if "fqphp.gxom.cn" in api_endpoint_template and content:
                        # 处理内容
                        if len(content) > 20:
                            content = content[:-20]

                        content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
                        content = re.sub(r'</?article>', '', content)
                        content = re.sub(r'<p[^>]*>', '\n    ', content)
                        content = re.sub(r'</p>', '', content)
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\\u003c|\\u003e', '', content)

                        content = re.sub(r'\n{3,}', '\n\n', content).strip()
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        formatted_content = '\n'.join(['    ' + line for line in lines])
                        return chapter_title, formatted_content

                    elif "api.cenguigui.cn" in api_endpoint_template and data.get("code") == 200 and content:
                        # 处理内容
                        content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
                        content = re.sub(r'</?article>', '', content)
                        content = re.sub(r'<p idx="\d+">', '\n', content)
                        content = re.sub(r'</p>', '\n', content)
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\\u003c|\\u003e', '', content)

                        if chapter_title and content.startswith(chapter_title):
                            content = content[len(chapter_title):].lstrip()

                        content = re.sub(r'\n{2,}', '\n', content).strip()
                        formatted_content = '\n'.join(['    ' + line if line.strip() else line for line in content.split('\n')])
                        return chapter_title, formatted_content

                    elif "lsjk.zyii.xyz" in api_endpoint_template and content:
                        # 处理内容
                        paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                        cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                        formatted_content = '\n'.join('    ' + line if line.strip() else line
                                                    for line in cleaned_content.split('\n'))
                        return chapter_title, formatted_content

                    elif "jingluo.love" in api_endpoint_template and content:
                        # 处理内容
                        content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
                        content = re.sub(r'</?article>', '', content)
                        content = re.sub(r'<p idx="\d+">', '\n', content)
                        content = re.sub(r'</p>', '\n', content)
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\\u003c|\\u003e', '', content)

                        if chapter_title and content.startswith(chapter_title):
                            content = content[len(chapter_title):].lstrip()

                        content = re.sub(r'\n{2,}', '\n', content).strip()
                        formatted_content = '\n'.join(['    ' + line if line.strip() else line for line in content.split('\n')])
                        return chapter_title, formatted_content

                except Exception as fallback_e:
                    log_func(f"原始URL也请求失败: {str(fallback_e)}")

            down_text.api_status[api_endpoint_template]["error_count"] += 1
            time.sleep(3)

    log_func(f"所有API尝试失败，无法下载章节 {chapter_id}")
    return None, None

def get_book_info(book_id: str, headers: Dict[str, str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """从网页获取书籍基本信息"""
    url = f'https://fanqienovel.com/page/{book_id}'
    try:
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()

        if not response.text or response.status_code != 200:
            return None, None, None

        try:
            soup = bs4.BeautifulSoup(response.text, 'lxml')
        except bs4.FeatureNotFound:
            soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # 获取书名
        name_element = soup.find('h1')
        name = name_element.text.strip() if name_element else None

        # 获取作者
        author_name = None
        author_name_element = soup.find('div', class_='author-name')
        if author_name_element:
            author_name_span = author_name_element.find('span', class_='author-name-text')
            if author_name_span:
                author_name = author_name_span.text.strip()

        # 获取简介
        description = None
        description_element = soup.find('div', class_='page-abstract-content')
        if description_element:
            description_p = description_element.find('p')
            if description_p:
                description = description_p.text.strip()

        return name, author_name, description

    except requests.exceptions.Timeout:
        return None, None, None
    except requests.exceptions.RequestException as e:
        return None, None, None
    except Exception as e:
        return None, None, None

def get_chapters_from_api(book_id: str, headers: Dict[str, str]) -> Optional[List[Dict[str, Any]]]:
    """从API获取章节列表"""
    api_url = f"https://fanqienovel.com/api/reader/directory/detail?bookId={book_id}"
    try:
        response = requests.get(api_url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()

        data = response.json()
        if data.get("code") != 0 or "data" not in data:
            return None

        all_item_ids = data["data"].get("allItemIds")
        item_data = data["data"].get("itemDataMap", {})

        if not all_item_ids:
            return None

        chapters = []
        for idx, chapter_id in enumerate(all_item_ids):
            chapter_info = item_data.get(str(chapter_id), {})
            title = chapter_info.get("title", f"第{idx+1}章")

            chapters.append({
                "id": str(chapter_id),
                "title": title,
                "index": idx
            })

        return chapters

    except Exception as e:
        return None

def load_status(save_path: str, book_id: str = None) -> Set[str]:
    """加载下载状态"""
    status_file = os.path.join(save_path, "download_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict) and book_id:
                    return set(data.get(book_id, []))
                return set()
        except:
            pass
    return set()

def save_status(save_path: str, book_id: str, downloaded: Set[str], logger_callback: Optional[callable] = None):
    """保存下载状态"""
    status_file = os.path.join(save_path, "download_status.json")
    try:
        # 尝试加载现有数据
        existing_data = {}
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, dict):
                        existing_data = {}
            except:
                existing_data = {}

        # 更新当前书籍的状态
        existing_data[book_id] = list(downloaded)

        # 保存到文件
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        if logger_callback:
            logger_callback(f"保存下载状态失败: {e}")
        else:
            print(f"保存下载状态失败: {e}")

class GUIdownloader:
    """GUI下载器类，用于在GUI环境中下载小说"""

    def __init__(self, book_id: str, save_path: str, status_callback: callable, progress_callback: callable):
        self.book_id = book_id
        self.save_path = save_path
        self.status_callback = status_callback
        self.progress_callback = progress_callback

        self.book_info = {}
        self.chapters = []
        self.downloaded_chapter_ids = set()
        self.output_file_path = ""
        self._stop_event = threading.Event()

    def _log_status(self, message: str):
        """记录状态信息"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

    def stop_download(self):
        """停止下载"""
        self._stop_event.set()
        self._log_status("Download stop requested.")

    def run(self):
        """运行下载任务（GUI调用的主方法）"""
        self.start_download()

    def start_download(self):
        """开始下载流程"""
        try:
            # 1. 获取书籍信息
            self._log_status("正在获取书籍信息...")
            headers = get_headers()
            name, author, description = get_book_info(self.book_id, headers)

            if not name:
                self._log_status(f"无法获取书籍ID {self.book_id} 的信息")
                return

            self.book_info = {
                'name': sanitize_filename(name),
                'author': author or "未知作者",
                'description': description or "无简介"
            }

            self._log_status(f"书名: {self.book_info['name']}")
            self._log_status(f"作者: {self.book_info['author']}")

            # 2. 获取章节列表
            self._log_status("正在获取章节列表...")
            self.chapters = get_chapters_from_api(self.book_id, headers)

            if not self.chapters:
                self._log_status("无法获取章节列表")
                return

            self._log_status(f"获取到 {len(self.chapters)} 个章节")

            # 3. 创建保存目录
            book_save_dir = os.path.join(self.save_path, self.book_info['name'])
            os.makedirs(book_save_dir, exist_ok=True)
            self.output_file_path = os.path.join(book_save_dir, f"{self.book_info['name']}.txt")

            # 4. 加载已下载状态
            self.downloaded_chapter_ids = load_status(book_save_dir, self.book_id)
            downloaded_count_start = len(self.downloaded_chapter_ids)
            self._log_status(f"检测到已下载 {downloaded_count_start} 章节")

            # 5. 下载章节
            todo_chapters = [ch for ch in self.chapters if ch["id"] not in self.downloaded_chapter_ids]
            if not todo_chapters:
                self._log_status("所有章节已是最新，无需下载")
                self.progress_callback(100)
                return

            self._log_status(f"开始下载 {len(todo_chapters)} 个章节...")

            # 存储下载内容
            temp_downloaded_content = {}
            downloaded_count_this_session = 0
            completed = 0
            max_workers = CONFIG["request"].get("max_workers", 5)

            def download_chapter(chapter_info):
                nonlocal downloaded_count_this_session, completed
                if self._stop_event.is_set():
                    return None

                self._log_status(f"下载章节 {chapter_info['index'] + 1}/{len(self.chapters)}: {chapter_info['title']}")
                
                # 重试机制
                for attempt in range(3):
                    api_title, content = down_text(chapter_info["id"], self.book_id, logger_callback=self._log_status)
                    if content:
                        return chapter_info, api_title, content
                    time.sleep(1 * (attempt + 1))  # 指数退避
                return None

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(download_chapter, ch): ch for ch in todo_chapters}
                for future in as_completed(futures):
                    if self._stop_event.is_set():
                        break

                    result = future.result()
                    if result:
                        chapter_info, api_title, content = result
                        temp_downloaded_content[chapter_info["index"]] = (chapter_info["title"], api_title or "", content)
                        self.downloaded_chapter_ids.add(chapter_info["id"])
                        save_status(book_save_dir, self.book_id, self.downloaded_chapter_ids, logger_callback=self._log_status)
                        downloaded_count_this_session += 1
                        self._log_status(f"成功下载章节 {chapter_info['title']}")

                    completed += 1
                    progress = int(completed / len(todo_chapters) * 100)
                    self.progress_callback(progress)

            # 6. 写入文件
            self._log_status("正在写入文件...")
            self._write_book_file(temp_downloaded_content)

            if not self._stop_event.is_set():
                self._log_status(f"下载完成！成功下载 {downloaded_count_this_session} 个章节")
                self.progress_callback(100)

        except Exception as e:
            self._log_status(f"下载过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

    def _write_book_file(self, temp_downloaded_content: Dict[int, Tuple[str, str, str]]):
        """写入书籍文件"""
        try:
            with open(self.output_file_path, 'w', encoding='utf-8') as f:
                # 写入书籍信息
                f.write(f"小说名: {self.book_info['name']}\n")
                f.write(f"作者: {self.book_info['author']}\n")
                f.write(f"内容简介: {self.book_info['description']}\n\n")

                # 按章节顺序写入内容
                for idx in range(len(self.chapters)):
                    chapter_info = self.chapters[idx]

                    if idx in temp_downloaded_content:
                        # 使用本次下载的内容
                        base_title, api_title, content = temp_downloaded_content[idx]
                        full_title = f"{base_title} {api_title}".strip()
                        f.write(f"{full_title}\n")
                        f.write(content + '\n\n')
                    elif chapter_info["id"] in self.downloaded_chapter_ids:
                        # 章节已存在但本次未下载，尝试重新获取
                        api_title, content = down_text(chapter_info["id"], self.book_id, logger_callback=self._log_status)
                        if content:
                            full_title = f"{chapter_info['title']} {api_title}".strip()
                            f.write(f"{full_title}\n")
                            f.write(content + '\n\n')
                        else:
                            f.write(f"{chapter_info['title']} - (内容未获取)\n\n")

            self._log_status(f"书籍文件已保存到: {self.output_file_path}")

        except Exception as e:
            self._log_status(f"写入文件时发生错误: {e}")
