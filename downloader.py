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
from urllib.parse import urlencode, quote

# 导入章节矫正模块
try:
    from chapter_corrector import correct_chapters, analyze_chapter_title
    CHAPTER_CORRECTION_AVAILABLE = True
except ImportError:
    print("警告: 章节矫正模块未找到，将跳过章节矫正功能")
    CHAPTER_CORRECTION_AVAILABLE = False

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

def get_headers() -> Dict[str, str]:
    """生成随机请求头"""
    # 预定义的用户代理列表，避免依赖fake_useragent的网络请求
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]

    try:
        # 尝试使用fake_useragent
        browsers = ['chrome', 'edge']
        browser = random.choice(browsers)

        if browser == 'chrome':
            user_agent = UserAgent().chrome
        else:
            user_agent = UserAgent().edge
    except Exception:
        # 如果fake_useragent失败，使用预定义的用户代理
        user_agent = random.choice(user_agents)

    return {
        "User-Agent": user_agent,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://fanqienovel.com/",
        "X-Requested-With": "XMLHttpRequest",
    }

def search_novels(query: str, page: int = 0, limit: int = 20) -> Optional[Dict]:
    """
    搜索番茄小说
    
    Args:
        query: 搜索关键词
        page: 页码，从0开始
        limit: 每页数量限制
        
    Returns:
        搜索结果字典，包含书籍列表等信息
    """
    try:
        url = "https://fq.66ds.de/api/search"
        
        params = {
            'query': query,
            'offset': page * limit,
            'limit': limit,
            'page': page,
            'aid': 1967,
            'isLoadMore': False
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Referer': f'https://fq.66ds.de/search/index.html?q={quote(query)}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"搜索小说时出错: {str(e)}")
        return None

def format_search_results(search_data: Dict) -> str:
    """
    格式化搜索结果为可读文本
    
    Args:
        search_data: 搜索API返回的数据
        
    Returns:
        格式化后的搜索结果文本
    """
    if not search_data or search_data.get('code') != 0:
        return "搜索失败，请检查网络连接或稍后再试"
    
    book_data = search_data.get('data', {}).get('book_data', [])
    if not book_data:
        return "未找到相关小说"
    
    result = f"找到 {len(book_data)} 本相关小说：\n\n"
    
    for i, book in enumerate(book_data, 1):
        book_id = book.get('book_id', '')
        book_name = book.get('book_name', '未知')
        author = book.get('author', '未知作者')
        read_count = book.get('read_count', '0')
        creation_status = "完结" if book.get('creation_status') == "0" else "连载中"
        abstract = book.get('abstract', '无简介')[:100] + ('...' if len(book.get('abstract', '')) > 100 else '')
        
        # 获取分类标签
        categories = []
        for tag in book.get('category_tags', []):
            categories.append(tag.get('category_name', ''))
        category_text = ' | '.join(categories) if categories else '无分类'
        
        result += f"{i}. 《{book_name}》\n"
        result += f"   作者: {author}\n"
        result += f"   ID: {book_id}\n"
        result += f"   状态: {creation_status}\n"
        result += f"   阅读量: {read_count}\n"
        result += f"   分类: {category_text}\n"
        result += f"   简介: {abstract}\n"
        result += f"   {'='*50}\n\n"
    
    return result

def get_enhanced_book_info(book_id: str) -> Optional[Dict]:
    """
    通过多个来源获取增强的书籍信息，优先使用最完整的数据
    
    Args:
        book_id: 书籍ID
        
    Returns:
        包含详细信息的字典
    """
    try:
        # 初始化结果字典
        enhanced_info = {
            'book_id': book_id,
            'book_name': None,
            'author': None,
            'description': None,
            'thumb_url': None,
            'read_count': None,
            'creation_status': None,
            'category_tags': [],
            'genre': None,
            'book_type': None
        }
        
        # 1. 先通过增强的get_book_info获取完整信息
        try:
            headers = get_headers()
            book_info = get_book_info(book_id, headers)

            # 使用官网信息作为基础
            if book_info:
                enhanced_info['book_name'] = book_info.get('name')
                enhanced_info['author'] = book_info.get('author')
                enhanced_info['description'] = book_info.get('description')
                enhanced_info['thumb_url'] = book_info.get('cover_url')
                enhanced_info['creation_status'] = book_info.get('status')
                enhanced_info['category_tags'] = book_info.get('tags', [])
                # 添加额外信息
                enhanced_info['word_count'] = book_info.get('word_count')
                enhanced_info['last_update'] = book_info.get('last_update')

        except Exception as e:
            print(f"获取基本书籍信息失败: {str(e)}")
        
        # 2. 通过搜索API获取详细信息
        search_info = None
        if enhanced_info['book_name']:
            # 如果有书名，用书名搜索
            search_result = search_novels(enhanced_info['book_name'], limit=5)
            if search_result and search_result.get('code') == 0:
                book_data = search_result.get('data', {}).get('book_data', [])
                
                # 查找匹配的书籍（只通过ID匹配，确保是同一本书）
                for book in book_data:
                    if book.get('book_id') == book_id:
                        search_info = book
                        break
                    # 移除按书名匹配，因为可能匹配到同名但不同作者的书
        
        # 3. 如果通过书名没找到，尝试通过作者搜索
        if not search_info and enhanced_info['author']:
            try:
                search_result = search_novels(enhanced_info['author'], limit=10)
                if search_result and search_result.get('code') == 0:
                    book_data = search_result.get('data', {}).get('book_data', [])
                    
                    # 查找匹配的书籍（只通过ID匹配）
                    for book in book_data:
                        if book.get('book_id') == book_id:
                            search_info = book
                            break
            except Exception as e:
                print(f"通过作者搜索失败: {str(e)}")
        
        # 4. 智能合并信息：优先使用官网信息，搜索API作为补充
        if search_info:
            # 书名：优先使用官网信息，如果官网没有才使用搜索结果
            if not enhanced_info['book_name'] and search_info.get('book_name') and search_info['book_name'].strip():
                enhanced_info['book_name'] = search_info['book_name']

            # 作者：优先使用官网信息，如果官网没有才使用搜索结果
            if not enhanced_info['author'] and search_info.get('author') and search_info['author'].strip():
                enhanced_info['author'] = search_info['author']

            # 简介：只有当 HTML 解析不到或等于默认时才用 API 描述
            search_desc = search_info.get('abstract', '').strip()
            if (not enhanced_info['description'] or enhanced_info['description'] == '暂无简介') and search_desc:
                enhanced_info['description'] = search_desc
            
            # 封面：优先使用官网信息，如果官网没有才使用搜索结果
            if not enhanced_info['thumb_url'] and search_info.get('thumb_url'):
                enhanced_info['thumb_url'] = search_info['thumb_url']
            
            if search_info.get('read_count'):
                enhanced_info['read_count'] = search_info['read_count']
            
            if search_info.get('creation_status') is not None:
                enhanced_info['creation_status'] = search_info['creation_status']
            
            # 分类标签：只有当 HTML 没解析到任何标签时才用 API
            if not enhanced_info['category_tags'] and search_info.get('category_tags'):
                enhanced_info['category_tags'] = search_info['category_tags']
            
            if search_info.get('genre') is not None:
                enhanced_info['genre'] = search_info['genre']
            
            if search_info.get('book_type') is not None:
                enhanced_info['book_type'] = search_info['book_type']
        
        # 5. 最终数据验证和清理
        # 确保基本信息不为空
        if not enhanced_info['book_name'] or enhanced_info['book_name'].strip() == '':
            enhanced_info['book_name'] = f"未知小说_{book_id}"
        
        if not enhanced_info['author'] or enhanced_info['author'].strip() == '':
            enhanced_info['author'] = "未知作者"
        
        if not enhanced_info['description'] or enhanced_info['description'].strip() == '':
            enhanced_info['description'] = "暂无简介"
        
        # 验证分类标签格式
        if enhanced_info['category_tags'] and not isinstance(enhanced_info['category_tags'], list):
            enhanced_info['category_tags'] = []
        
        return enhanced_info
        
    except Exception as e:
        print(f"获取增强书籍信息时出错: {str(e)}")
        # 返回基本信息作为备用
        return {
            'book_id': book_id,
            'book_name': f"未知小说_{book_id}",
            'author': "未知作者",
            'description': "暂无简介",
            'thumb_url': None,
            'read_count': None,
            'creation_status': None,
            'category_tags': []
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
            "raw_title": raw_title,
            "url": f"https://fanqienovel.com{a_tag['href']}",
            "index": idx
        })
    return chapters

def batch_download_chapters(item_ids, headers):
    """Dlmily模式下载章节内容"""
    if not CONFIG["batch_config"]["enabled"]:
        print("Dlmily下载功能未启用")
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
            print(f"Dlmily下载失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print(f"Dlmily下载异常！")
        return None

def validate_chapter_mapping(item_ids, results):
    """验证章节ID映射是否正确"""
    if not results or not item_ids:
        return False

    # 检查所有请求的章节ID是否都在结果中
    missing_ids = [chapter_id for chapter_id in item_ids if chapter_id not in results]
    if missing_ids:
        print(f"警告：以下章节ID在结果中缺失: {missing_ids}")

    # 检查结果中是否有意外的章节ID
    unexpected_ids = [chapter_id for chapter_id in results.keys() if chapter_id not in item_ids]
    if unexpected_ids:
        print(f"警告：结果中包含意外的章节ID: {unexpected_ids}")

    return len(missing_ids) == 0

def validate_chapter_integrity(chapter_results, total_chapters, chapters_info=None):
    """验证章节完整性和连续性"""
    if not chapter_results:
        print("警告：没有章节结果需要验证")
        return False, []

    issues = []
    downloaded_indices = set(chapter_results.keys())

    # 1. 检查章节索引连续性
    if downloaded_indices:
        min_idx = min(downloaded_indices)
        max_idx = max(downloaded_indices)

        # 检查是否有中间章节缺失
        missing_indices = []
        for i in range(min_idx, max_idx + 1):
            if i not in downloaded_indices:
                missing_indices.append(i + 1)  # 转为人类可读的章节号

        if missing_indices:
            issue = f"检测到章节缺失，缺失章节号: {missing_indices}"
            issues.append(issue)
            print(f"完整性检查 - {issue}")

    # 2. 检查章节内容完整性
    empty_content_chapters = []
    for idx, result in chapter_results.items():
        if not result.get("content", "").strip():
            empty_content_chapters.append(idx + 1)

    if empty_content_chapters:
        issue = f"检测到空内容章节: 第{empty_content_chapters}章"
        issues.append(issue)
        print(f"完整性检查 - {issue}")

    # 3. 检查章节标题合理性（如果提供了章节信息）
    if chapters_info:
        title_mismatch_chapters = []
        for idx, result in chapter_results.items():
            if idx < len(chapters_info):
                expected_title = chapters_info[idx]["title"]
                actual_title = result.get("title", "")

                # 简单的标题匹配检查
                if (expected_title and actual_title and
                    expected_title not in actual_title and
                    actual_title not in expected_title):
                    title_mismatch_chapters.append({
                        "chapter": idx + 1,
                        "expected": expected_title,
                        "actual": actual_title
                    })

        if title_mismatch_chapters:
            issue = f"检测到标题不匹配章节: {len(title_mismatch_chapters)}个"
            issues.append(issue)
            print(f"完整性检查 - {issue}")
            for mismatch in title_mismatch_chapters[:3]:  # 只显示前3个
                print(f"  第{mismatch['chapter']}章: 期望'{mismatch['expected']}', 实际'{mismatch['actual']}'")

    # 4. 检查总体完整性
    completion_rate = len(downloaded_indices) / total_chapters if total_chapters > 0 else 0
    if completion_rate < 0.95:  # 如果完成率低于95%
        issue = f"章节完成率较低: {completion_rate:.1%} ({len(downloaded_indices)}/{total_chapters})"
        issues.append(issue)
        print(f"完整性检查 - {issue}")

    is_valid = len(issues) == 0
    if is_valid:
        print(f"章节完整性检查通过: {len(downloaded_indices)}/{total_chapters} 章节，完成率 {completion_rate:.1%}")
    else:
        print(f"章节完整性检查发现 {len(issues)} 个问题")

    return is_valid, issues

def check_rabbits0209_limit(chapters, config=None):
    """
    检查rabbits0209模式下的章节限制
    
    Args:
        chapters: 待下载的章节列表
        config: 配置字典，如果为None则使用全局CONFIG
        
    Returns:
        tuple: (is_over_limit, max_chapters, suggested_batches)
            - is_over_limit: 是否超过限制
            - max_chapters: 最大章节限制
            - suggested_batches: 建议的批次数
    """
    try:
        # 导入配置
        if config is None:
            from config import CONFIG
            config = CONFIG
        
        # 获取rabbits0209配置
        request_config = config.get("request", {})
        enable_limit = request_config.get("rabbits0209_enable_limit", True)
        max_chapters = request_config.get("rabbits0209_max_chapters", 30)
        
        # 如果未启用限制，返回不超限
        if not enable_limit:
            return False, max_chapters, 1
        
        chapter_count = len(chapters) if chapters else 0
        
        # 检查是否超过限制
        is_over_limit = chapter_count > max_chapters
        
        # 计算建议的批次数
        if is_over_limit:
            suggested_batches = (chapter_count + max_chapters - 1) // max_chapters
        else:
            suggested_batches = 1
        
        return is_over_limit, max_chapters, suggested_batches
        
    except Exception as e:
        print(f"警告: 检查rabbits0209章节限制时发生错误 {str(e)}")
        # 发生错误时返回安全的默认值
        return False, 30, 1

def create_limited_batches(chapters, config=None):
    """
    根据rabbits0209章节限制创建批次
    
    Args:
        chapters: 待下载的章节列表
        config: 配置字典，如果为None则使用全局CONFIG
        
    Returns:
        list: 分批后的章节列表，每个元素是一个章节批次
    """
    try:
        # 导入配置
        if config is None:
            from config import CONFIG
            config = CONFIG
        
        # 获取rabbits0209配置
        request_config = config.get("request", {})
        enable_limit = request_config.get("rabbits0209_enable_limit", True)
        max_chapters = request_config.get("rabbits0209_max_chapters", 30)
        
        if not chapters:
            return []
        
        # 如果未启用限制，返回单个批次
        if not enable_limit:
            return [chapters]
        
        # 确保章节按索引排序
        sorted_chapters = sorted(chapters, key=lambda x: x.get("index", 0))
        
        # 分批处理
        batches = []
        for i in range(0, len(sorted_chapters), max_chapters):
            batch = sorted_chapters[i:i + max_chapters]
            batches.append(batch)
        
        print(f"章节分批完成: 总计 {len(sorted_chapters)} 章节，分为 {len(batches)} 批，每批最多 {max_chapters} 章节")
        
        return batches
        
    except Exception as e:
        print(f"警告: 创建章节批次时发生错误 {str(e)}")
        # 发生错误时返回原始章节作为单个批次
        return [chapters] if chapters else []

def qwq_batch_download_chapters(item_ids, headers):
    """rabbits0209模式批量下载章节内容，采用严格的ID验证，确保章节顺序正确"""
    try:
        # 1. 构建请求
        item_ids_str = ",".join(item_ids)
        url = f"https://qwq.tutuxka.top/api/index.php?api=content&item_ids={item_ids_str}&api_type=batch"
        
        print(f"rabbits0209批量请求URL: {url}")
        print(f"请求章节数: {len(item_ids)}")

        qwq_headers = headers.copy()
        qwq_headers['Accept-Encoding'] = 'gzip, deflate'

        # 2. 发送请求
        response = requests.get(
            url,
            headers=qwq_headers,
            timeout=CONFIG["request_timeout"],
            verify=False
        )
        response.raise_for_status() # 抛出HTTP错误

        # 3. 解析和严格验证响应
        data = response.json()
        
        if isinstance(data, dict) and data.get("error"):
            print(f"rabbits0209 API返回错误: {data.get('error')}")
            return None

        results = {}
        chapter_list = []

        # 统一处理不同格式的数据源，最终得到一个章节列表
        if isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), list):
            chapter_list = data["data"]
            print(f"处理标准API响应格式，包含 {len(chapter_list)} 个章节。")
        elif isinstance(data, list):
            chapter_list = data
            print(f"处理直接列表响应格式，包含 {len(chapter_list)} 个章节。")
        else:
            print(f"警告：API返回了未知的或非列表格式的数据，批量下载失败。数据类型: {type(data)}")
            return None # 未知格式，拒绝处理

        # 4. 严格的ID匹配
        if not chapter_list:
            print("警告：API返回的章节列表为空，批量下载失败。")
            return None

        # 检查返回的第一个项目是否包含'id'，这是关键的验证步骤
        if not isinstance(chapter_list[0], dict):
            print(f"警告：API返回的章节数据不是字典格式，实际类型: {type(chapter_list[0])}")
            print("将自动降级为单章模式重试，以确保顺序正确。")
            return None

        # 调试：打印第一个章节的键名
        first_chapter_keys = list(chapter_list[0].keys())
        print(f"调试：第一个章节包含的字段: {first_chapter_keys}")

        # 检查是否有ID字段（可能是不同的字段名）
        id_field = None
        possible_id_fields = ['id', 'item_id', 'chapter_id', 'chapterId', 'itemId']
        for field in possible_id_fields:
            if field in chapter_list[0]:
                id_field = field
                break

        # 如果没有找到ID字段，但有content字段，尝试按顺序处理
        if not id_field and 'content' in chapter_list[0]:
            print("警告：API返回的数据缺少ID字段，但包含content，尝试按顺序处理...")
            # 按请求顺序处理章节
            for i, chapter_data in enumerate(chapter_list):
                if i < len(item_ids) and isinstance(chapter_data, dict):
                    chapter_id = item_ids[i]  # 使用请求的ID顺序
                    content = chapter_data.get("content", "")
                    title = chapter_data.get("title", "")

                    if content and content.strip():  # 确保内容不为空
                        processed_content = process_chapter_content(content)
                        results[chapter_id] = {
                            "content": processed_content,
                            "title": title
                        }
                        print(f"  ✓ 处理章节 {i+1}/{len(chapter_list)}: {title[:30]}...")
                    else:
                        print(f"  ✗ 跳过空章节 {i+1}: {title}")

            if results:
                print(f"✅ 成功按顺序处理了 {len(results)}/{len(chapter_list)} 个章节")
                return results
            else:
                print("❌ 按顺序处理失败，所有章节内容为空")
                return None

        if not id_field:
            print("警告：API返回的章节数据中缺少ID字段，无法进行安全匹配，批量下载失败。")
            print(f"尝试的字段名: {possible_id_fields}")
            print("将自动降级为单章模式重试，以确保顺序正确。")
            return None

        # 遍历返回的章节，只接受ID在请求列表中的章节
        matched_ids = set()
        for chapter_data in chapter_list:
            if not isinstance(chapter_data, dict): continue

            chapter_id = str(chapter_data.get(id_field, ''))
            content = chapter_data.get("content", "")

            if chapter_id in item_ids and content:
                processed_content = process_chapter_content(content)
                results[chapter_id] = {
                    "content": processed_content,
                    "title": chapter_data.get("title", "")
                }
                matched_ids.add(chapter_id)
            elif chapter_id not in item_ids:
                print(f"警告：API返回了未请求的章节ID {chapter_id}，已忽略。")

        # 5. 最终验证
        if not results:
            print("警告：批量下载未能成功匹配任何章节。")
            return None

        print(f"批量下载验证通过，成功匹配 {len(results)}/{len(item_ids)} 个章节。")
        return results

    except requests.exceptions.RequestException as e:
        print(f"rabbits0209批量请求失败: {str(e)}")
        return None
    except json.JSONDecodeError:
        print(f"rabbits0209批量下载JSON解析失败。响应内容: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"rabbits0209批量下载发生未知异常: {str(e)}")
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

            # 对qwq API特殊处理，避免Brotli压缩问题
            if api_name == "qwq":
                print(f"qwq单章请求URL: {current_endpoint}")
                qwq_headers = headers.copy()
                qwq_headers['Accept-Encoding'] = 'gzip, deflate'  # 移除br压缩
                response = requests.get(
                    current_endpoint,
                    headers=qwq_headers,
                    timeout=CONFIG["request_timeout"],
                    verify=False
                )
            else:
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
                "error_count": max(0, down_text.api_status[endpoint["url"]]["error_count"] - 1)
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

            elif api_name == "qwq":
                if content:
                    processed_content = process_chapter_content(content)
                    return chapter_title, processed_content
                else:
                    # 检查是否有错误信息
                    if isinstance(data, dict) and "error" in data:
                        print(f"qwq API返回错误: {data.get('error')}")
                        if "trace" in data:
                            print(f"错误详情: {data['trace']}")
                    else:
                        print(f"qwq API返回空内容")

            print(f"API返回空内容，继续尝试下一个API...")
            down_text.api_status[endpoint["url"]]["error_count"] += 1

        except Exception as e:
            print(f"API请求失败: {str(e)}")
            down_text.api_status[endpoint["url"]]["error_count"] += 1
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

        # 合并数据，生成按API顺序的章节列表并确保标题正确
        final_chapters = []
        for idx, chapter_id in enumerate(chapter_ids):
            # 查找网页解析的对应章节
            web_chapter = next((ch for ch in chapters if ch["id"] == chapter_id), None)

            if web_chapter:
                raw_title = web_chapter.get("raw_title", web_chapter.get("title", "")).strip()
                # 智能判断是否需要添加章节号前缀
                # 如果原始标题本身不包含 "第X章" 或 "番外" 等标识，则添加
                if not re.match(r'^(第[一二三四五六七八九十百千\d]+章|番外|特别篇|if线)', raw_title, re.IGNORECASE):
                    title = f"第{idx+1}章 {raw_title}"
                else:
                    # 否则直接使用原始标题，因为它已经包含了章节信息
                    title = raw_title
            else:
                # 如果在网页解析结果中找不到，则创建一个基础标题
                title = f"第{idx+1}章"

            final_chapters.append({
                "id": chapter_id,
                "title": title,
                "index": idx
            })

        # 应用章节矫正功能
        if CHAPTER_CORRECTION_AVAILABLE and CONFIG.get("chapter_correction", {}).get("enabled", True):
            try:
                corrected_chapters, correction_issues = correct_chapters(final_chapters)

                if correction_issues and CONFIG.get("chapter_correction", {}).get("show_correction_report", True):
                    print("=== 章节矫正报告 ===")
                    for issue in correction_issues:
                        print(f"  - {issue}")
                    print(f"已对 {len(final_chapters)} 个章节进行智能排序矫正")
                    print("=" * 20)

                # 更新章节索引以保持一致性
                for idx, chapter in enumerate(corrected_chapters):
                    chapter["index"] = idx

                return corrected_chapters

            except Exception as e:
                print(f"章节矫正过程中发生错误: {str(e)}")
                print("将使用原始章节顺序")
                return final_chapters

        return final_chapters

    except Exception as e:
        print(f"获取章节列表失败: {str(e)}")
        return None


def apply_post_download_correction(downloaded_chapters, book_info=None):
    """
    下载完成后应用章节矫正，提供更好的用户反馈
    
    Args:
        downloaded_chapters: 已下载的章节列表
        book_info: 书籍信息
    
    Returns:
        (corrected_chapters, correction_report)
    """
    try:
        if not CHAPTER_CORRECTION_AVAILABLE:
            return downloaded_chapters, "章节矫正模块不可用"
            
        correction_config = CONFIG.get("chapter_correction", {})
        if not correction_config.get("enabled", True):
            return downloaded_chapters, "章节矫正功能已禁用"
        
        print("\n🔧 正在进行下载后章节矫正...")
        
        # 准备章节数据用于矫正
        chapters_for_correction = []
        for i, chapter in enumerate(downloaded_chapters):
            chapters_for_correction.append({
                "id": chapter.get("id", str(i)),
                "title": chapter.get("title", f"第{i+1}章"),
                "index": i
            })
        
        # 执行矫正
        corrected_chapters, issues = correct_chapters(chapters_for_correction)
        
        # 检查是否有顺序变化
        original_order = [ch["title"] for ch in chapters_for_correction]
        corrected_order = [ch["title"] for ch in corrected_chapters]
        has_changes = original_order != corrected_order
        
        # 生成报告
        report_lines = []
        report_lines.append("=== 📚 下载后章节矫正报告 ===")
        
        if book_info:
            report_lines.append(f"书籍: {book_info.get('book_name', '未知')}")
        
        report_lines.append(f"总章节数: {len(downloaded_chapters)}")
        
        if has_changes:
            report_lines.append("✅ 章节顺序已重新优化")
            
            # 显示关键变化
            changes_count = sum(1 for o, c in zip(original_order, corrected_order) if o != c)
            report_lines.append(f"调整了 {changes_count} 个章节的位置")
            
            # 显示前3个重要变化
            shown = 0
            for i, (orig, corr) in enumerate(zip(original_order, corrected_order)):
                if orig != corr and shown < 3:
                    report_lines.append(f"  位置 {i+1}: '{orig}' → '{corr}'")
                    shown += 1
            
            if changes_count > 3:
                report_lines.append(f"  ... 还有 {changes_count - 3} 个其他调整")
        else:
            report_lines.append("ℹ️ 章节顺序已是最优，无需调整")
        
        if issues:
            report_lines.append("🔍 处理的问题:")
            for issue in issues:
                report_lines.append(f"  - {issue}")
        
        report_lines.append("=" * 30)
        report = "\n".join(report_lines)
        
        # 显示报告
        if correction_config.get("show_correction_report", True):
            print(report)
        
        # 如果有变化，重新构建下载章节数据
        if has_changes:
            final_chapters = []
            for corrected_ch in corrected_chapters:
                # 找到对应的原始章节数据
                original_ch = next(
                    (ch for ch in downloaded_chapters if ch.get("id") == corrected_ch["id"]), 
                    None
                )
                
                if original_ch:
                    # 保持原有数据结构，只更新标题和索引
                    updated_ch = original_ch.copy()
                    updated_ch["title"] = corrected_ch["title"]
                    updated_ch["corrected_index"] = len(final_chapters)
                    final_chapters.append(updated_ch)
            
            return final_chapters, report
        else:
            return downloaded_chapters, report
        
    except Exception as e:
        error_msg = f"章节矫正过程中发生错误: {str(e)}"
        print(error_msg)
        return downloaded_chapters, error_msg

def get_book_info(book_id, headers):
    """获取书籍完整信息 - 增强版，从官网HTML解析完整信息"""
    url = f'https://fanqienovel.com/page/{book_id}'
    try:
                # 使用普通浏览器头请求 HTML 页面，避免 Ajax JSON 响应
        html_headers = {k: v for k, v in headers.items() if k not in ['Accept', 'X-Requested-With']}
        html_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        response = requests.get(url, headers=html_headers, timeout=CONFIG["request_timeout"])

        if response.status_code != 200:
            print(f"网络请求失败，状态码: {response.status_code}")
            return None

        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # 获取书名
        name_element = soup.find('h1')
        name = name_element.text.strip() if name_element else "未知书名"

        # 获取作者
        author_name = "未知作者"
        author_name_element = soup.find('div', class_='author-name')
        if author_name_element:
            author_name_span = author_name_element.find('span', class_='author-name-text')
            if author_name_span:
                author_name = author_name_span.text.strip()

        # 获取简介
        description = "暂无简介"
        description_element = soup.find('div', class_='page-abstract-content')
        if description_element:
            description_p = description_element.find('p')
            if description_p:
                # 保持换行格式
                description = description_p.get_text(separator='\n', strip=True)
            else:
                description = description_element.get_text(separator='\n', strip=True)

        # 获取封面图片URL
        cover_url = ""
        cover_element = soup.find('img', class_='book-cover-img')
        if cover_element and cover_element.get('src'):
            cover_url = cover_element.get('src')

        # 获取完结状态和类型标签
        status = "连载中"  # 默认状态
        tags = []

        # 解析标签信息
        label_elements = soup.find_all('span', class_='info-label-yellow') + soup.find_all('span', class_='info-label-grey')
        for label in label_elements:
            label_text = label.text.strip()
            if label_text in ['已完结', '连载中', '完结']:
                status = '已完结' if label_text in ['已完结', '完结'] else '连载中'
            else:
                tags.append(label_text)

        # 获取字数信息
        word_count = ""
        word_element = soup.find('div', class_='info-count-word')
        if word_element:
            detail_span = word_element.find('span', class_='detail')
            text_span = word_element.find('span', class_='text')
            if detail_span and text_span:
                word_count = f"{detail_span.text.strip()}{text_span.text.strip()}"

        # 获取最后更新时间
        last_update = ""
        time_element = soup.find('span', class_='info-last-time')
        if time_element:
            last_update = time_element.text.strip()

        print(f"成功获取书籍信息: {name}")
        print(f"作者: {author_name}")
        print(f"状态: {status}")
        print(f"标签: {', '.join(tags) if tags else '无'}")
        print(f"字数: {word_count}")
        print(f"最后更新: {last_update}")

        return {
            'name': name,
            'author': author_name,
            'description': description,
            'cover_url': cover_url,
            'status': status,
            'tags': tags,
            'word_count': word_count,
            'last_update': last_update
        }

    except Exception as e:
        print(f"获取书籍信息失败: {str(e)}")
        return None

def load_status(save_path, book_id=None):
    """加载下载状态"""
    # 优先使用基于书籍ID的状态文件格式
    try:
        from config import CONFIG as USER_CONFIG
        status_file_format = USER_CONFIG.get("file", {}).get("status_file_format", ".{book_id}.download_status")
        if book_id and "{book_id}" in status_file_format:
            status_filename = status_file_format.format(book_id=book_id)
        else:
            # 回退到原来的格式
            status_filename = CONFIG["status_file"]
    except:
        # 如果配置加载失败，使用默认格式
        if book_id:
            status_filename = f".{book_id}.download_status"
        else:
            status_filename = CONFIG["status_file"]
    
    # 创建状态文件子目录
    status_dir = os.path.join(save_path, ".tomato_status")
    os.makedirs(status_dir, exist_ok=True)
    
    # 新的状态文件路径
    new_status_file = os.path.join(status_dir, status_filename)
    
    # 检查新位置的状态文件
    if os.path.exists(new_status_file):
        try:
            with open(new_status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                return set()
        except:
            pass
    
    # 向后兼容：检查旧位置的状态文件
    old_status_file = os.path.join(save_path, status_filename)
    if os.path.exists(old_status_file):
        try:
            with open(old_status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    downloaded_set = set(data)
                    # 迁移到新位置
                    try:
                        with open(new_status_file, 'w', encoding='utf-8') as new_f:
                            json.dump(list(downloaded_set), new_f, ensure_ascii=False, indent=2)
                        # 删除旧文件
                        os.remove(old_status_file)
                        print(f"已迁移状态文件到新位置: {status_dir}")
                    except:
                        pass  # 迁移失败时静默处理
                    return downloaded_set
                return set()
        except:
            pass
    
    return set()

def save_status(save_path, downloaded, book_id=None):
    """保存下载状态"""
    # 优先使用基于书籍ID的状态文件格式
    try:
        from config import CONFIG as USER_CONFIG
        status_file_format = USER_CONFIG.get("file", {}).get("status_file_format", ".{book_id}.download_status")
        if book_id and "{book_id}" in status_file_format:
            status_filename = status_file_format.format(book_id=book_id)
        else:
            # 回退到原来的格式
            status_filename = CONFIG["status_file"]
    except:
        # 如果配置加载失败，使用默认格式
        if book_id:
            status_filename = f".{book_id}.download_status"
        else:
            status_filename = CONFIG["status_file"]
    
    # 创建状态文件子目录
    status_dir = os.path.join(save_path, ".tomato_status")
    os.makedirs(status_dir, exist_ok=True)
    
    status_file = os.path.join(status_dir, status_filename)
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(list(downloaded), f, ensure_ascii=False, indent=2)


def Run(book_id, save_path):
    """运行下载"""
    def signal_handler(sig, frame):
        print("\n检测到程序中断，正在保存已下载内容...")
        write_downloaded_chapters_in_order()
        save_status(save_path, downloaded, book_id)
        print(f"已保存 {len(downloaded)} 个章节的进度")
        sys.exit(0)

    def write_downloaded_chapters_in_order():
        """按章节顺序写入，包含完整性检查"""
        if not chapter_results:
            return

        # 执行章节完整性检查
        is_valid, issues = validate_chapter_integrity(chapter_results, len(chapters), chapters)

        if not is_valid:
            print("警告：章节完整性检查发现问题，但仍将写入已下载的章节")
            for issue in issues:
                print(f"  - {issue}")

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"小说名: {name}\n作者: {author_name}\n内容简介: {description}\n\n")

            # 如果有完整性问题，在文件开头添加警告
            if not is_valid:
                f.write("=" * 50 + "\n")
                f.write("警告：本文件可能存在章节完整性问题\n")
                for issue in issues:
                    f.write(f"- {issue}\n")
                f.write("=" * 50 + "\n\n")

            for idx in range(len(chapters)):
                if idx in chapter_results:
                    result = chapter_results[idx]
                    title = result["title"]
                    f.write(f"{title}\n{result['content']}\n\n")

    # 信号处理
    signal.signal(signal.SIGINT, signal_handler)

    try:
        headers = get_headers()
        chapters = get_chapters_from_api(book_id, headers)
        if not chapters:
            print("未找到任何章节，请检查小说ID是否正确。")
            return

        book_info = get_book_info(book_id, headers)
        if book_info:
            name = book_info.get('name', f"未知小说_{book_id}")
            author_name = book_info.get('author', "未知作者")
            description = book_info.get('description', "暂无简介")
        else:
            name = f"未知小说_{book_id}"
            author_name = "未知作者"
            description = "暂无简介"
            description = "无简介"

        downloaded = load_status(save_path, book_id)
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

        # Dlmily下载 - 命令行模式默认使用Dlmily下载
        if (CONFIG["batch_config"]["enabled"] and
            any(ep["name"] == "qyuing" for ep in CONFIG["api_endpoints"])):
            print("启用Dlmily下载模式...")
            batch_size = CONFIG["batch_config"]["max_batch_size"]

            with tqdm(total=len(todo_chapters), desc="Dlmily下载进度") as pbar:
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
                                    "title": chap["title"],
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
            save_status(save_path, downloaded, book_id)

        # rabbits0209下载
        def download_task(chapter):
            nonlocal success_count
            try:
                title, content = down_text(chapter["id"], headers, book_id)
                if content:
                    with lock:
                        chapter_results[chapter["index"]] = {
                            "title": title or chapter["title"],
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

                with tqdm(total=len(todo_chapters), desc="rabbits0209下载进度") as pbar:
                    for _ in as_completed(futures):
                        pbar.update(1)

            write_downloaded_chapters_in_order()
            save_status(save_path, downloaded, book_id)
            todo_chapters = failed_chapters.copy()
            failed_chapters = []

            if todo_chapters:
                time.sleep(1)

        print(f"下载完成！成功下载 {success_count} 个章节")

    except Exception as e:
        print(f"运行错误: {str(e)}")
        if 'downloaded' in locals():
            write_downloaded_chapters_in_order()
            save_status(save_path, downloaded, book_id)

# GUI下载器类，用于兼容现有的GUI代码
class GUIdownloader:
    """GUI下载器类，用于在GUI环境中下载小说"""

    def __init__(self, book_id: str, save_path: str, status_callback: callable, progress_callback: callable, 
                 output_format: str = "TXT", generate_epub_when_txt: bool = False, download_mode: str = "batch"):
        self.book_id = book_id
        self.save_path = save_path
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.output_format = output_format
        self.generate_epub_when_txt = generate_epub_when_txt
        self.download_mode = download_mode  # 'batch'(Dlmily) or 'single'(rabbits0209)
        self.stop_flag = False
        self.start_time = time.time()

    def _generate_book_header(self, name: str, author_name: str, description: str, enhanced_info: dict = None) -> str:
        """生成包含详细信息的书籍头部"""
        import datetime
        
        header = f"书名: {name}\n"
        header += f"作者: {author_name}\n"
        
        if enhanced_info:
            # 添加详细信息
            read_count = enhanced_info.get('read_count')
            creation_status = enhanced_info.get('creation_status')
            category_tags = enhanced_info.get('category_tags', [])
            # 确保列表项为 dict，便于后续使用 tag.get
            category_tags = [{'category_name': tag} if isinstance(tag, str) else tag for tag in category_tags]
            book_id = enhanced_info.get('book_id', '')
            
            if read_count:
                header += f"阅读量: {read_count}\n"
            
            if creation_status is not None:
                # 处理不同类型的状态值
                if creation_status == "0" or creation_status == 0:
                    status_text = "完结"
                elif creation_status == "1" or creation_status == 1:
                    status_text = "连载中"
                else:
                    status_text = f"未知状态({creation_status})"
                header += f"连载状态: {status_text}\n"
            
            if category_tags:
                categories = [tag.get('category_name', '') for tag in category_tags if tag.get('category_name')]
                if categories:
                    header += f"分类: {' | '.join(categories)}\n"
            
            if book_id:
                header += f"书籍ID: {book_id}\n"
        
        header += f"下载时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"来源: 番茄小说\n"
        header += f"内容简介: {description}\n"
        header += f"{'='*50}\n\n"
        
        return header

    def stop_download(self):
        """停止下载"""
        self.stop_flag = True
        if self.status_callback:
            self.status_callback("下载已停止")

    def run(self):
        """运行下载"""
        # 使用用户配置的线程数覆盖默认值
        try:
            from config import CONFIG as user_config
            CONFIG["max_workers"] = user_config.get("request", {}).get("max_workers", CONFIG.get("max_workers", 4))
            # 覆盖请求限速
            CONFIG["request_rate_limit"] = user_config.get("request", {}).get("request_rate_limit", CONFIG.get("request_rate_limit", 0))
            # 覆盖请求超时
            CONFIG["request_timeout"] = user_config.get("request", {}).get("timeout", CONFIG.get("request_timeout", 15))
            # 注意：不覆盖下载模式，优先使用GUI传入的值
            # self.download_mode 保持GUI传入的值不变
        except Exception:
            pass
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

            # 获取书籍信息（智能合并多个来源的数据）
            enhanced_info = get_enhanced_book_info(self.book_id)
            
            if enhanced_info:
                name = enhanced_info.get('book_name', '未知书名')
                author_name = enhanced_info.get('author', '未知作者')
                description = enhanced_info.get('description', '暂无简介')
                
                if self.status_callback:
                    self.status_callback(f"获取到详细书籍信息: 《{name}》 - {author_name}")
                    
                    # 显示额外的详细信息
                    read_count = enhanced_info.get('read_count')
                    creation_status = enhanced_info.get('creation_status')
                    category_tags = enhanced_info.get('category_tags', [])
                    # 确保列表项为 dict，便于后续使用 tag.get
                    category_tags = [{'category_name': tag} if isinstance(tag, str) else tag for tag in category_tags]
                    word_count = enhanced_info.get('word_count')
                    last_update = enhanced_info.get('last_update')

                    if read_count:
                        self.status_callback(f"阅读量: {read_count}")

                    if creation_status is not None:
                        # 转换状态码为可读文本
                        if creation_status == "0" or creation_status == 0:
                            status_text = "完结"
                        elif creation_status == "1" or creation_status == 1:
                            status_text = "连载中"
                        else:
                            status_text = f"未知状态({creation_status})"
                        self.status_callback(f"状态: {status_text}")

                    if word_count:
                        self.status_callback(f"字数: {word_count}")

                    if last_update:
                        self.status_callback(f"最后更新: {last_update}")

                    if category_tags:
                        # 处理不同格式的标签
                        if isinstance(category_tags, list) and category_tags:
                            # 如果是字符串列表，直接使用
                            if isinstance(category_tags[0], str):
                                self.status_callback(f"分类标签: {' | '.join(category_tags)}")
                            # 如果是字典列表（来自搜索API），提取category_name
                            elif isinstance(category_tags[0], dict):
                                categories = [tag.get('category_name', '') for tag in category_tags if tag.get('category_name')]
                                if categories:
                                    self.status_callback(f"分类标签: {' | '.join(categories)}")

                    if enhanced_info.get('thumb_url'):
                        self.status_callback("检测到封面图片，EPUB版本将包含封面")
            else:
                # 如果完全获取失败，使用备用信息
                name = f"未知小说_{self.book_id}"
                author_name = "未知作者"
                description = "无简介"
                enhanced_info = None
                
                if self.status_callback:
                    self.status_callback("无法获取书籍详细信息，使用默认信息")

            if self.status_callback:
                self.status_callback(f"开始下载：《{name}》")

            downloaded = load_status(self.save_path, self.book_id)
            todo_chapters = [ch for ch in chapters if ch["id"] not in downloaded]

            # 计算总章节数和已下载章节数
            total_chapters = len(chapters)
            already_downloaded = len(downloaded)

            # 调试信息
            if self.status_callback:
                self.status_callback(f"总章节数: {total_chapters}, 已下载: {already_downloaded}, 待下载: {len(todo_chapters)}")

            # 设置初始进度（基于已下载的章节）
            initial_progress = int(already_downloaded / total_chapters * 100) if total_chapters > 0 else 0
            if self.progress_callback:
                self.progress_callback(initial_progress)
                
            # 调试信息
            if self.status_callback:
                self.status_callback(f"设置初始进度: {initial_progress}%")

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
            failed_chapters = []
            chapter_results = {}
            import threading
            lock = threading.Lock()

            # 记录Dlmily下载的成功数量，避免重复计算
            batch_success_count = 0

            # 根据下载模式设置API列表 - 必须在Dlmily下载判断之前设置
            if self.download_mode == 'single':
                # rabbits0209模式：强制使用qwq API，清除其他API避免Dlmily下载误判
                # qwq API统一使用item_ids参数，单章和批量都使用相同的基础URL格式
                CONFIG["api_endpoints"] = [{"name": "qwq", "url": "https://qwq.tutuxka.top/api/index.php?api=content&item_ids={chapter_id}"}]
                # 同时禁用Dlmily下载配置，确保不会触发Dlmily下载
                CONFIG["batch_config"]["enabled"] = False
                if self.status_callback:
                    self.status_callback("已设置为rabbits0209下载模式，使用qwq API")

            # Dlmily下载模式 - 只有在明确选择batch模式时才执行
            if self.download_mode == 'batch' and\
                CONFIG["batch_config"]["enabled"] and\
                any(ep["name"] == "qyuing" for ep in CONFIG["api_endpoints"]):

                if self.status_callback:
                    self.status_callback("启用Dlmily下载模式...")

                batch_size = CONFIG["batch_config"]["max_batch_size"]
                total_batches = (len(todo_chapters) + batch_size - 1) // batch_size

                for batch_idx in range(0, len(todo_chapters), batch_size):
                    if self.stop_flag:
                        break

                    batch = todo_chapters[batch_idx:batch_idx + batch_size]
                    current_batch = batch_idx // batch_size + 1

                    if self.status_callback:
                        self.status_callback(f"Dlmily下载第 {current_batch}/{total_batches} 批 ({len(batch)} 章节)")

                    item_ids = [chap["id"] for chap in batch]

                    # Dlmity立即重试机制
                    immediate_retry_enabled = CONFIG.get("request", {}).get("immediate_retry", True)
                    batch_results = None
                    batch_retry_count = 0
                    max_batch_retries = CONFIG.get("request", {}).get("max_retries", 3) if immediate_retry_enabled else 1

                    while batch_retry_count < max_batch_retries and not batch_results:
                        if batch_retry_count > 0 and immediate_retry_enabled:
                            print(f"[Dlmity批次 {current_batch}] 第 {batch_retry_count + 1} 次尝试...")
                            if self.status_callback:
                                self.status_callback(f"Dlmity批次 {current_batch} 立即重试中 ({batch_retry_count + 1}/{max_batch_retries})...")
                            time.sleep(1)  # 重试前短暂等待

                        batch_results = batch_download_chapters(item_ids, headers)
                        batch_retry_count += 1

                        if not batch_results and batch_retry_count < max_batch_retries and immediate_retry_enabled:
                            print(f"[Dlmity批次 {current_batch}] 第 {batch_retry_count} 次尝试失败，将立即重试")

                    if not batch_results:
                        if immediate_retry_enabled:
                            print(f"[Dlmity批次 {current_batch}] 在 {batch_retry_count} 次立即重试后仍失败")
                            if self.status_callback:
                                self.status_callback(f"Dlmity第 {current_batch} 批在 {batch_retry_count} 次立即重试后仍失败，将使用rabbits0209模式重试")
                        else:
                            print(f"[Dlmity批次 {current_batch}] 下载失败（立即重试已禁用）")
                            if self.status_callback:
                                self.status_callback(f"Dlmity第 {current_batch} 批下载失败，将使用rabbits0209模式重试")
                        failed_chapters.extend(batch)
                        continue

                    if batch_retry_count > 1 and immediate_retry_enabled:
                        print(f"[Dlmity批次 {current_batch}] 总共尝试了 {batch_retry_count} 次，成功！")

                    # 处理批量下载结果
                    batch_success = 0
                    for chap in batch:
                        if self.stop_flag:
                            break

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
                                batch_success += 1
                                batch_success_count += 1
                        else:
                            with lock:
                                failed_chapters.append(chap)

                    # 批次完成后更新进度（而不是在每个章节后）
                    current_downloaded = already_downloaded + batch_success_count
                    progress = int(current_downloaded / total_chapters * 100)
                    
                    # 调试信息
                    if self.status_callback:
                        self.status_callback(f"进度调试: 已下载={already_downloaded}, 批次成功={batch_success_count}, 总章节={total_chapters}, 进度={progress}%")
                    
                    if self.progress_callback:
                        self.progress_callback(progress)

                    if self.status_callback:
                        self.status_callback(f"第 {current_batch} 批完成，成功下载 {batch_success}/{len(batch)} 章节")

                # Dlmily下载结果已存入chapter_results, 无需立即写入
                save_status(self.save_path, downloaded, self.book_id)
                todo_chapters = failed_chapters.copy()
                failed_chapters = []

                if self.status_callback and todo_chapters:
                    self.status_callback(f"Dlmily下载完成，剩余 {len(todo_chapters)} 章节将使用rabbits0209模式下载")

            # rabbits0209下载模式 - 使用qwq批量请求
            single_chapter_success_count = 0  # 单独计算rabbits0209下载的成功数
            
            # 应用rabbits0209章节限制检查
            if todo_chapters and self.download_mode == 'single':
                try:
                    from config import CONFIG as user_config
                    is_over_limit, max_chapters, suggested_batches = check_rabbits0209_limit(todo_chapters, user_config)
                    
                    if is_over_limit:
                        if self.status_callback:
                            self.status_callback(f"检测到章节数({len(todo_chapters)})超过rabbits0209限制({max_chapters}章)")
                            self.status_callback(f"将自动分为 {suggested_batches} 个批次进行下载")
                    else:
                        if self.status_callback:
                            self.status_callback(f"章节数({len(todo_chapters)})在限制范围内，开始下载")
                except Exception as e:
                    print(f"警告: 应用rabbits0209章节限制时发生错误 {str(e)}")
            
            if self.status_callback and todo_chapters:
                self.status_callback("开始rabbits0209批量请求模式...")

            # 添加重试循环机制
            attempt = 1
            max_attempts = CONFIG.get("max_retries", 3)
            all_single_results = {}  # 收集所有成功下载的章节

            # 获取rabbits0209模式的有效批量大小（考虑章节限制）
            try:
                # 使用全局CONFIG，避免重复导入
                from config import CONFIG as user_config
                
                # 获取用户配置的批量大小
                user_batch_size = user_config.get("request", {}).get("single_batch_size", None)
                
                # 获取章节限制配置
                enable_limit = user_config.get("request", {}).get("rabbits0209_enable_limit", True)
                max_chapters = user_config.get("request", {}).get("rabbits0209_max_chapters", 30)
                
                if user_batch_size is not None:
                    # 用户明确配置了批量大小，rabbits0209 API最大只能接受30章
                    configured_batch_size = min(user_batch_size, 30)  # 最大限制30章
                    print(f"用户配置的rabbits0209批量大小: {configured_batch_size}")
                else:
                    # 未配置时，使用线程数作为批量大小（GUI可控制）
                    max_workers = CONFIG.get("max_workers", 4)
                    configured_batch_size = min(max_workers * 5, 30)  # 线程数的5倍，最大30
                    print(f"根据线程数({max_workers})计算rabbits0209批量大小: {configured_batch_size}")
                
                # 应用章节限制
                if enable_limit and self.download_mode == 'single':
                    single_batch_size = min(configured_batch_size, max_chapters)
                    if single_batch_size != configured_batch_size:
                        print(f"应用rabbits0209章节限制: 批量大小从 {configured_batch_size} 调整为 {single_batch_size}")
                        if self.status_callback:
                            self.status_callback(f"应用章节限制: 每批最多 {single_batch_size} 章节")
                else:
                    single_batch_size = configured_batch_size
                    if self.status_callback and not enable_limit:
                        self.status_callback(f"未启用章节限制，使用配置的批量大小: {single_batch_size}")
                    
            except Exception as e:
                print(f"获取批量大小配置失败: {e}，使用默认值30")
                single_batch_size = 30

            # 确保批量大小在合理范围内（rabbits0209 API限制）
            if single_batch_size < 1:
                single_batch_size = 1
                print("批量大小调整为最小值1")
            elif single_batch_size > 30:
                single_batch_size = 30
                print("批量大小调整为最大值30（rabbits0209 API限制）")

            while todo_chapters and attempt <= max_attempts:
                if self.stop_flag:
                    break

                if attempt > 1 and self.status_callback:
                    self.status_callback(f"第 {attempt} 次重试，剩余 {len(todo_chapters)} 个章节...")

                failed_chapters_this_round = []

                # 保持失败章节的完整上下文信息，包括原始顺序
                chapter_context_map = {}
                for ch in todo_chapters:
                    chapter_context_map[ch["id"]] = {
                        "index": ch["index"],
                        "title": ch["title"],
                        "original_chapter": ch,
                        "retry_count": getattr(ch, 'retry_count', 0) + 1
                    }

                # 使用rabbits0209批量请求
                if self.status_callback:
                    self.status_callback(f"使用rabbits0209批量请求，每批 {single_batch_size} 章节...")
                
                # 记录批量下载开始时间和统计信息
                batch_start_time = time.time()
                total_batches_count = (len(todo_chapters) + single_batch_size - 1) // single_batch_size
                print(f"rabbits0209批量下载开始:")
                print(f"  - 总章节数: {len(todo_chapters)}")
                print(f"  - 批次数: {total_batches_count}")
                print(f"  - 每批最多: {single_batch_size}章")
                print(f"  - 章节限制: {'启用' if enable_limit else '禁用'}")
                if enable_limit:
                    print(f"  - 限制值: {max_chapters}章")
                    if configured_batch_size > max_chapters:
                        print(f"  - 批量大小已从 {configured_batch_size} 调整为 {single_batch_size}")
                print(f"  - 开始时间: {time.strftime('%H:%M:%S', time.localtime(batch_start_time))}")

                for batch_start in range(0, len(todo_chapters), single_batch_size):
                    if self.stop_flag:
                        break

                    batch_chapters = todo_chapters[batch_start:batch_start + single_batch_size]
                    # 按原始索引排序，确保顺序正确
                    batch_chapters = sorted(batch_chapters, key=lambda x: x["index"])
                    batch_item_ids = [ch["id"] for ch in batch_chapters]

                    batch_num = batch_start // single_batch_size + 1
                    total_batches = (len(todo_chapters) + single_batch_size - 1) // single_batch_size

                    # 记录批次开始时间
                    batch_time_start = time.time()
                    
                    if self.status_callback:
                        self.status_callback(f"rabbits0209批量请求第 {batch_num}/{total_batches} 批 ({len(batch_chapters)} 章节)")

                    print(f"[批次 {batch_num}] 开始时间: {time.strftime('%H:%M:%S', time.localtime(batch_time_start))}")
                    print(f"[批次 {batch_num}] 章节索引范围: {batch_chapters[0]['index']}-{batch_chapters[-1]['index']}")
                    print(f"[批次 {batch_num}] 章节IDs: {batch_item_ids[:3]}{'...' if len(batch_item_ids) > 3 else ''}")

                    # 根据配置决定是否使用立即重试机制
                    immediate_retry_enabled = CONFIG.get("request", {}).get("immediate_retry", True)
                    batch_results = None
                    batch_retry_count = 0
                    max_batch_retries = CONFIG.get("request", {}).get("max_retries", 3) if immediate_retry_enabled else 1

                    while batch_retry_count < max_batch_retries and not batch_results:
                        if batch_retry_count > 0 and immediate_retry_enabled:
                            print(f"[批次 {batch_num}] 第 {batch_retry_count + 1} 次尝试...")
                            if self.status_callback:
                                self.status_callback(f"批次 {batch_num} 立即重试中 ({batch_retry_count + 1}/{max_batch_retries})...")
                            time.sleep(1)  # 重试前短暂等待

                        batch_results = qwq_batch_download_chapters(batch_item_ids, headers)
                        batch_retry_count += 1

                        if not batch_results and batch_retry_count < max_batch_retries and immediate_retry_enabled:
                            print(f"[批次 {batch_num}] 第 {batch_retry_count} 次尝试失败，将立即重试")

                    # 记录批次结束时间
                    batch_time_end = time.time()
                    batch_duration = batch_time_end - batch_time_start
                    print(f"[批次 {batch_num}] 结束时间: {time.strftime('%H:%M:%S', time.localtime(batch_time_end))}")
                    print(f"[批次 {batch_num}] 耗时: {batch_duration:.2f}秒")

                    if batch_retry_count > 1 and immediate_retry_enabled:
                        print(f"[批次 {batch_num}] 总共尝试了 {batch_retry_count} 次")
                    elif not immediate_retry_enabled:
                        print(f"[批次 {batch_num}] 立即重试已禁用，失败批次将在最后统一重试")

                    if batch_results:
                        # 严格按照请求顺序处理批量下载结果，使用上下文信息验证
                        successful_in_batch = 0
                        print(f"[批次 {batch_num}] 处理下载结果: 收到 {len(batch_results)} 个章节数据")
                        
                        for chapter in batch_chapters:
                            chapter_id = chapter["id"]
                            if chapter_id in batch_results:
                                chapter_data = batch_results[chapter_id]
                                content = chapter_data.get("content", "")
                                title = chapter_data.get("title", "")

                                # 验证章节上下文信息
                                if chapter_id in chapter_context_map:
                                    expected_index = chapter_context_map[chapter_id]["index"]
                                    expected_title = chapter_context_map[chapter_id]["title"]

                                    # 验证索引一致性
                                    if chapter["index"] != expected_index:
                                        print(f"警告：章节 {chapter_id} 索引不一致，期望 {expected_index}，实际 {chapter['index']}")

                                    # 可选：验证标题相似性（简单检查）
                                    if title and expected_title and title not in expected_title and expected_title not in title:
                                        print(f"警告：章节 {chapter_id} 标题可能不匹配，期望包含 '{expected_title}'，实际 '{title}'")

                                if content:
                                    # 使用章节的原始索引确保正确顺序，并记录上下文信息
                                    if chapter_id in chapter_context_map:
                                        original_index = chapter_context_map[chapter_id]["index"]
                                        original_chapter = chapter_context_map[chapter_id]["original_chapter"]
                                        retry_count = chapter_context_map[chapter_id]["retry_count"]

                                        all_single_results[original_index] = (original_chapter, title, content)
                                        print(f"批量下载成功：第{original_index+1}章 {chapter['title']} (重试{retry_count}次)")
                                    else:
                                        all_single_results[chapter["index"]] = (chapter, title, content)
                                        print(f"批量下载成功：第{chapter['index']+1}章 {chapter['title']}")

                                    downloaded.add(chapter["id"])
                                    save_status(self.save_path, downloaded, self.book_id)
                                    single_chapter_success_count += 1
                                    successful_in_batch += 1

                                    if self.status_callback:
                                        current_pos = already_downloaded + batch_success_count + single_chapter_success_count
                                        self.status_callback(f"已下载: {title or chapter['title']} ({current_pos}/{total_chapters})")
                                    if self.progress_callback:
                                        progress = int(current_pos / total_chapters * 100)
                                        self.progress_callback(progress)
                                else:
                                    # 保留完整上下文信息用于重试
                                    if chapter_id in chapter_context_map:
                                        failed_chapter = chapter_context_map[chapter_id]["original_chapter"].copy()
                                        failed_chapter['retry_count'] = chapter_context_map[chapter_id]['retry_count']
                                        failed_chapters_this_round.append(failed_chapter)
                                    else:
                                        failed_chapters_this_round.append(chapter)
                                    print(f"章节 {chapter_id} (第{chapter['index']+1}章: {chapter['title']}) 内容为空")
                            else:
                                # 批量结果中没有这个章节，保持原始顺序信息并标记为失败
                                if chapter_id in chapter_context_map:
                                    failed_chapter = chapter_context_map[chapter_id]["original_chapter"].copy()
                                    failed_chapter['retry_count'] = chapter_context_map[chapter_id]['retry_count']
                                    failed_chapters_this_round.append(failed_chapter)
                                else:
                                    failed_chapters_this_round.append(chapter)
                                print(f"章节 {chapter_id} (第{chapter['index']+1}章: {chapter['title']}) 不在批量结果中")

                        # 记录批次完成统计
                        print(f"[批次 {batch_num}] 完成统计: 成功={successful_in_batch}/{len(batch_chapters)}, 失败={len(batch_chapters)-successful_in_batch}")
                        print(f"[批次 {batch_num}] 成功率: {successful_in_batch/len(batch_chapters)*100:.1f}%")
                        
                        if self.status_callback:
                            self.status_callback(f"第 {batch_num} 批完成: {successful_in_batch}/{len(batch_chapters)} 章节成功")
                    else:
                        # 整批失败，保持章节顺序信息并加入重试列表
                        print(f"[批次 {batch_num}] 完全失败，章节索引: {[ch['index'] for ch in batch_chapters]}")
                        if immediate_retry_enabled:
                            print(f"[批次 {batch_num}] 失败原因: 批量请求在 {batch_retry_count} 次立即重试后仍返回空结果")
                            if self.status_callback:
                                self.status_callback(f"第 {batch_num} 批在 {batch_retry_count} 次立即重试后仍失败，将在下轮重试")
                        else:
                            print(f"[批次 {batch_num}] 失败原因: 批量请求返回空结果（立即重试已禁用）")
                            if self.status_callback:
                                self.status_callback(f"第 {batch_num} 批失败，将在最后统一重试")
                        failed_chapters_this_round.extend(batch_chapters)

                    # 批次间延迟
                    time.sleep(CONFIG["request_rate_limit"])



                # 更新待重试章节列表 - 按原始索引排序保持顺序
                todo_chapters = sorted(failed_chapters_this_round.copy(), key=lambda x: x["index"])
                
                if todo_chapters:
                    print(f"本轮重试失败章节索引: {[ch['index'] for ch in todo_chapters]}")
                    if self.status_callback:
                        index_ranges = f"第{todo_chapters[0]['index']+1}章" + (f"-第{todo_chapters[-1]['index']+1}章" if len(todo_chapters) > 1 else "")
                        self.status_callback(f"本轮剩余失败章节: {len(todo_chapters)}个 ({index_ranges})")
                
                attempt += 1

                # 如果还有失败章节且未达到最大重试次数，等待后重试
                if todo_chapters and attempt <= max_attempts:
                    if self.status_callback:
                        self.status_callback(f"等待 2 秒后进行第 {attempt} 次重试...")
                    time.sleep(2)
            
            # 记录rabbits0209下载完成统计
            batch_end_time = time.time()
            total_batch_duration = batch_end_time - batch_start_time
            print(f"rabbits0209批量下载完成统计:")
            print(f"  - 总耗时: {total_batch_duration:.2f}秒")
            print(f"  - 总批次数: {total_batches_count}")
            print(f"  - 每批最大章节数: {single_batch_size}")
            print(f"  - 章节限制状态: {'已启用' if enable_limit else '未启用'}")
            if enable_limit:
                print(f"  - 章节限制值: {max_chapters}章")
            print(f"  - 成功章节数: {single_chapter_success_count}")
            print(f"  - 失败章节数: {len(todo_chapters)}")
            print(f"  - 成功率: {single_chapter_success_count/(single_chapter_success_count+len(todo_chapters))*100:.1f}%" if (single_chapter_success_count+len(todo_chapters)) > 0 else "  - 成功率: 0%")
            
            if self.status_callback:
                if len(todo_chapters) == 0:
                    self.status_callback(f"rabbits0209下载完成: 全部 {single_chapter_success_count} 章节下载成功")
                else:
                    self.status_callback(f"rabbits0209下载完成: {single_chapter_success_count} 章节成功，{len(todo_chapters)} 章节失败")
            # 统一写入逻辑：在所有下载尝试结束后，对所有成功下载的章节进行排序和写入
            if self.status_callback:
                self.status_callback("所有下载尝试已完成，开始整合和写入最终文件...")

            # 1. 将 rabbits0209 下载的所有成功结果合并到主章节结果字典中
            if all_single_results:
                for idx, (chapter, title, content) in all_single_results.items():
                    # 确保即使在重试后，结果也被正确地放入主容器
                    if idx not in chapter_results:
                        chapter_results[idx] = {
                            "base_title": chapter["title"],
                            "api_title": title,
                            "content": content
                        }

            # 2. 只有在至少下载了一个章节的情况下才执行写入
            if chapter_results:
                # 对所有收集到的结果进行最终的完整性检查
                is_valid, issues = validate_chapter_integrity(chapter_results, len(chapters), chapters)
                if not is_valid:
                    if self.status_callback:
                        self.status_callback(f"警告：检测到 {len(issues)} 个章节完整性问题。")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    if self.status_callback:
                        self.status_callback("章节完整性检查通过。")

                # 3. 核心修复：始终使用覆盖模式('w')重写整个文件，以确保最终顺序绝对正确
                try:
                    with open(output_file_path, 'w', encoding='utf-8') as f:
                        f.write(self._generate_book_header(name, author_name, description, enhanced_info))

                        if not is_valid:
                            f.write("=" * 50 + "\n")
                            f.write("警告：本书籍文件可能存在以下完整性问题：\n")
                            for issue in issues:
                                f.write(f"- {issue}\n")
                            f.write("=" * 50 + "\n\n")

                        # 严格按照章节的原始索引排序并写入
                        written_count = 0
                        sorted_indices = sorted(chapter_results.keys())
                        for idx in sorted_indices:
                            result = chapter_results[idx]
                            # 优先使用API返回的标题，如果为空则使用我们自己生成的标题
                            title_display = result["api_title"] or result["base_title"]
                            f.write(f"{title_display}\n{result['content']}\n\n")
                            written_count += 1
                    
                    if self.status_callback:
                        range_text = f"第{sorted_indices[0]+1}-{sorted_indices[-1]+1}章" if sorted_indices else "无"
                        self.status_callback(f"文件写入成功: 共写入 {written_count} 个章节 (范围: {range_text})")

                    # 🔧 应用下载后章节矫正
                    try:
                        if self.status_callback:
                            self.status_callback("正在进行下载后章节矫正检查...")
                        
                        # 准备已下载章节数据用于矫正
                        downloaded_chapters_for_correction = []
                        for idx in sorted_indices:
                            result = chapter_results[idx]
                            downloaded_chapters_for_correction.append({
                                "id": str(idx),
                                "title": result["api_title"] or result["base_title"],
                                "content": result["content"],
                                "index": idx
                            })
                        
                        # 执行下载后矫正
                        corrected_chapters, correction_report = apply_post_download_correction(
                            downloaded_chapters_for_correction, 
                            enhanced_info
                        )
                        
                        # 检查是否有矫正变化
                        original_titles = [ch["title"] for ch in downloaded_chapters_for_correction]
                        corrected_titles = [ch["title"] for ch in corrected_chapters]
                        
                        if original_titles != corrected_titles:
                            # 有矫正变化，重新写入文件
                            if self.status_callback:
                                self.status_callback("检测到章节顺序需要优化，正在重新生成文件...")
                            
                            with open(output_file_path, 'w', encoding='utf-8') as f:
                                f.write(self._generate_book_header(name, author_name, description, enhanced_info))
                                
                                # 写入矫正报告
                                f.write("=" * 50 + "\n")
                                f.write("📚 章节矫正信息\n")
                                f.write("=" * 50 + "\n")
                                f.write(correction_report + "\n\n")
                                
                                # 按矫正后的顺序写入章节
                                for chapter in corrected_chapters:
                                    f.write(f"{chapter['title']}\n{chapter['content']}\n\n")
                            
                            if self.status_callback:
                                self.status_callback("✅ 章节矫正完成，文件已按最优顺序重新生成")
                        else:
                            if self.status_callback:
                                self.status_callback("ℹ️ 章节顺序已是最优，无需调整")
                        
                        # 在GUI中显示矫正报告摘要
                        if self.status_callback and correction_report:
                            # 提取关键信息显示
                            if "章节顺序已重新优化" in correction_report:
                                self.status_callback("📋 矫正摘要: 章节顺序已优化")
                            elif "处理的问题" in correction_report:
                                self.status_callback("📋 矫正摘要: 发现并处理了章节问题")
                            else:
                                self.status_callback("📋 矫正摘要: 章节检查完成")
                                
                    except Exception as correction_error:
                        print(f"下载后章节矫正失败: {str(correction_error)}")
                        if self.status_callback:
                            self.status_callback(f"章节矫正过程中出现问题: {str(correction_error)}")

                except Exception as e:
                    error_msg = f"错误: 最终文件写入失败: {str(e)}"
                    if self.status_callback: self.status_callback(error_msg)
                    print(error_msg)
            else:
                if self.status_callback:
                    self.status_callback("没有任何成功下载的章节，无需写入文件。")

            # 报告最终失败的章节（按章节顺序）
            if todo_chapters and self.status_callback:
                failed_chapter_numbers = [ch['index'] + 1 for ch in sorted(todo_chapters, key=lambda x: x['index'])]
                failed_ranges = []
                start = failed_chapter_numbers[0]
                end = failed_chapter_numbers[0]
                
                # 将连续章节合并为范围显示
                for i in range(1, len(failed_chapter_numbers)):
                    if failed_chapter_numbers[i] == end + 1:
                        end = failed_chapter_numbers[i]
                    else:
                        if start == end:
                            failed_ranges.append(f"第{start}章")
                        else:
                            failed_ranges.append(f"第{start}-{end}章")
                        start = end = failed_chapter_numbers[i]
                
                # 添加最后一个范围
                if start == end:
                    failed_ranges.append(f"第{start}章")
                else:
                    failed_ranges.append(f"第{start}-{end}章")
                
                self.status_callback(f"警告：{len(todo_chapters)}个章节在{max_attempts}次重试后仍然失败: {', '.join(failed_ranges)}")

            # 计算总成功数和最终统计
            total_success_count = batch_success_count + single_chapter_success_count
            final_progress = int((already_downloaded + total_success_count) / total_chapters * 100)
            
            # 最终验证和统计
            if self.status_callback:
                success_rate = (total_success_count / len(todo_chapters) * 100) if todo_chapters else 100
                self.status_callback(f"下载完成！本次成功 {total_success_count}/{len(chapters)-already_downloaded} 章节 (成功率: {success_rate:.1f}%)")
                self.status_callback(f"总进度: {already_downloaded + total_success_count}/{total_chapters} 章节 ({final_progress}%)")

            # 检查是否需要生成EPUB
            if self.output_format == "EPUB" or (self.output_format == "TXT" and self.generate_epub_when_txt):
                try:
                    from utils import generate_enhanced_epub, generate_epub, sanitize_filename, EBOOKLIB_AVAILABLE
                    
                    if not EBOOKLIB_AVAILABLE:
                        if self.status_callback:
                            self.status_callback("警告：ebooklib未安装，无法生成EPUB文件")
                    else:
                        if self.status_callback:
                            self.status_callback("正在生成增强版EPUB文件...")
                            
                        # 清理文件名
                        safe_name = sanitize_filename(name)
                        txt_file_path = os.path.join(self.save_path, f"{safe_name}.txt")
                        
                        if os.path.exists(txt_file_path):
                            # 优先使用增强版EPUB生成（包含详细信息和封面）
                            if enhanced_info:
                                success = generate_enhanced_epub(
                                    txt_file_path=txt_file_path,
                                    output_dir=self.save_path,
                                    book_info=enhanced_info
                                )
                            else:
                                # 回退到基础EPUB生成
                                success = generate_epub(
                                    txt_file_path=txt_file_path,
                                    output_dir=self.save_path,
                                    book_title=safe_name,
                                    author=author_name,
                                    description=description
                                )
                            
                            if success:
                                if self.status_callback:
                                    epub_type = "增强版EPUB" if enhanced_info else "基础EPUB"
                                    self.status_callback(f"{epub_type}文件生成成功！")
                            else:
                                if self.status_callback:
                                    self.status_callback("EPUB文件生成失败")
                        else:
                            if self.status_callback:
                                self.status_callback("警告：找不到TXT文件，无法生成EPUB")
                                
                except ImportError:
                    if self.status_callback:
                        self.status_callback("错误：无法导入epub生成模块")
                except Exception as e:
                    if self.status_callback:
                        self.status_callback(f"EPUB生成过程中出错: {str(e)}")

            if self.progress_callback:
                self.progress_callback(final_progress)

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"下载过程中发生错误: {str(e)}")
            print(f"下载异常详情: {str(e)}")
            import traceback
            traceback.print_exc()

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
