#!/usr/bin/env python3
"""
番茄小说下载器 - 命令行版本
提供无GUI的命令行下载功能
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
        print("无法连接到Tor网络，请确保Tor服务正在运行，将不能正常下载章节！")
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
    "max_workers": 5,
    "max_retries": 3,
    "request_timeout": 15,
    "status_file": "chapter.json",
    "request_rate_limit": 0.4,
    "api_endpoints": [
        "https://fqphp.gxom.cn/content?item_id={chapter_id}",
        "https://api.cenguigui.cn/api/tomato/content.php?item_id={chapter_id}",
        "https://lsjk.zyii.xyz:3666/content?item_id={chapter_id}",
        "http://nu1.jingluo.love/content?item_id={chapter_id}",
        "http://nu2.jingluo.love/content?item_id={chapter_id}"
    ],
    "api_keys": {
        "fqphp.gxom.cn": "BkmpOhGYbhFv"
    },
    "cloudflare_proxy": {
        "enabled": False,
        "proxy_domain": "",
        "fallback_to_original": True,
        "test_endpoint": "/test"
    }
}

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
    from urllib.parse import urlparse
    parsed = urlparse(url)

    # 构建反代URL：proxy_domain + 原URL的路径和查询参数
    proxy_url = f"{proxy_domain}{parsed.path}"
    if parsed.query:
        proxy_url += f"?{parsed.query}"

    return proxy_url

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

def down_text(chapter_id, headers, book_id=None):
    """下载章节内容"""
    content = ""
    chapter_title = ""

    # 初始化API端点状态
    if not hasattr(down_text, "api_status"):
        down_text.api_status = {endpoint: {
            "last_response_time": float('inf'),
            "error_count": 0,
            "last_try_time": 0
        } for endpoint in CONFIG["api_endpoints"]}

    # 顺序尝试API
    for api_endpoint in CONFIG["api_endpoints"]:
        current_endpoint = api_endpoint.format(chapter_id=chapter_id)
        down_text.api_status[api_endpoint]["last_try_time"] = time.time()

        try:
            # 随机延迟
            time.sleep(random.uniform(0.1, 0.5))

            # 添加密钥参数
            if "fqphp.gxom.cn" in api_endpoint:
                separator = "&" if "?" in current_endpoint else "?"
                current_endpoint += f"{separator}key={CONFIG['api_keys']['fqphp.gxom.cn']}"

            # 应用Cloudflare Workers反代
            proxy_endpoint = apply_cloudflare_proxy(current_endpoint)

            start_time = time.time()
            response = make_request(
                proxy_endpoint,
                headers=headers.copy(),
                timeout=CONFIG["request_timeout"],
                verify=False,
                use_tor=True
            )

            response_time = time.time() - start_time
            down_text.api_status[api_endpoint].update({
                "last_response_time": response_time,
                "error_count": max(0, down_text.api_status[api_endpoint]["error_count"] - 1)
            })

            data = response.json()
            content = data.get("data", {}).get("content", "")
            chapter_title = data.get("data", {}).get("title", "")

            if "fqphp.gxom.cn" in api_endpoint and content:
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

            elif "api.cenguigui.cn" in api_endpoint and data.get("code") == 200 and content:
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

            elif "lsjk.zyii.xyz" in api_endpoint and content:
                # 处理内容
                paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                formatted_content = '\n'.join('    ' + line if line.strip() else line
                                            for line in cleaned_content.split('\n'))
                return chapter_title, formatted_content

            elif "jingluo.love" in api_endpoint and content:
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

            print(f"API端点 {api_endpoint} 返回空内容，继续尝试下一个API...")
            down_text.api_status[api_endpoint]["error_count"] += 1

        except Exception as e:
            print(f"API端点 {api_endpoint} 请求失败: {str(e)}")

            # 如果启用了反代且失败，尝试使用原始URL
            proxy_config = CONFIG.get("cloudflare_proxy", {})
            if (proxy_config.get("enabled", False) and
                proxy_config.get("fallback_to_original", True) and
                proxy_endpoint != current_endpoint):

                print(f"反代请求失败，尝试使用原始URL: {current_endpoint}")
                try:
                    start_time = time.time()
                    response = make_request(
                        current_endpoint,
                        headers=headers.copy(),
                        timeout=CONFIG["request_timeout"],
                        verify=False,
                        use_tor=True
                    )

                    response_time = time.time() - start_time
                    down_text.api_status[api_endpoint].update({
                        "last_response_time": response_time,
                        "error_count": max(0, down_text.api_status[api_endpoint]["error_count"] - 1)
                    })

                    data = response.json()
                    content = data.get("data", {}).get("content", "")
                    chapter_title = data.get("data", {}).get("title", "")

                    # 处理内容的逻辑与上面相同
                    if "fqphp.gxom.cn" in api_endpoint and content:
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

                    elif "api.cenguigui.cn" in api_endpoint and data.get("code") == 200 and content:
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

                    elif "lsjk.zyii.xyz" in api_endpoint and content:
                        # 处理内容
                        paragraphs = re.findall(r'<p idx="\d+">(.*?)</p>', content)
                        cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())
                        formatted_content = '\n'.join('    ' + line if line.strip() else line
                                                    for line in cleaned_content.split('\n'))
                        return chapter_title, formatted_content

                    elif "jingluo.love" in api_endpoint and content:
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
                    print(f"原始URL也请求失败: {str(fallback_e)}")

            down_text.api_status[api_endpoint]["error_count"] += 1
            time.sleep(3)

    print(f"所有API尝试失败，无法下载章节 {chapter_id}")
    return None, None

def get_chapters_from_api(book_id, headers):
    """从API获取章节列表（包含完整标题）"""
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
                # 使用网页解析的完整标题
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

def main():
    """主函数"""
    print("番茄小说下载器 - 命令行版本")
    print("=" * 40)

    # 获取用户输入
    book_id = input("请输入小说ID: ").strip()
    if not book_id:
        print("小说ID不能为空")
        return

    save_path = input("请输入保存路径 (默认: downloads): ").strip()
    if not save_path:
        save_path = "downloads"

    # 创建保存目录
    os.makedirs(save_path, exist_ok=True)

    # 询问是否启用Tor
    use_tor = input("是否启用Tor代理? (y/N): ").strip().lower()
    if use_tor in ['y', 'yes']:
        enable_tor_support()

    print(f"开始下载小说 ID: {book_id}")
    print(f"保存路径: {save_path}")

    try:
        headers = get_headers()

        # 获取书籍信息
        name, author_name, description = get_book_info(book_id, headers)
        if not name:
            print("无法获取书籍信息")
            return

        print(f"书名: {name}")
        print(f"作者: {author_name}")
        print(f"简介: {description}")

        # 获取章节列表
        chapters = get_chapters_from_api(book_id, headers)
        if not chapters:
            print("未找到任何章节")
            return

        print(f"共找到 {len(chapters)} 个章节")

        # 检查已下载状态
        downloaded = load_status(save_path)
        todo_chapters = [ch for ch in chapters if ch["id"] not in downloaded]

        if not todo_chapters:
            print("所有章节已下载完成")
            return

        print(f"需要下载 {len(todo_chapters)} 个章节")

        # 开始下载
        output_file = os.path.join(save_path, f"{name}.txt")
        success_count = 0

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")

        for i, chapter in enumerate(tqdm(todo_chapters, desc="下载进度")):
            try:
                _, content = down_text(chapter["id"], headers, book_id)
                if content:
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(f'{chapter["title"]}\n')
                        f.write(content + '\n\n')

                    downloaded.add(chapter["id"])
                    save_status(save_path, downloaded)
                    success_count += 1
                else:
                    print(f"下载失败: {chapter['title']}")

                # 添加延迟
                time.sleep(CONFIG["request_rate_limit"])

            except KeyboardInterrupt:
                print("\n用户中断下载")
                break
            except Exception as e:
                print(f"下载章节 {chapter['title']} 时出错: {e}")

        print(f"下载完成！成功下载 {success_count} 个章节")
        print(f"文件保存在: {output_file}")

    except Exception as e:
        print(f"下载过程中发生错误: {e}")

if __name__ == "__main__":
    main()
