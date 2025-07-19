"""
网络工具模块

包含网络请求、连接检查等网络相关的工具函数
"""

import requests
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse


def make_request(url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                data: Optional[Dict[str, Any]] = None, timeout: int = 15,
                max_retries: int = 3, retry_delay: float = 1.0) -> Optional[requests.Response]:
    """
    发送HTTP请求，带重试机制
    
    Args:
        url: 请求URL
        method: 请求方法
        headers: 请求头
        data: 请求数据
        timeout: 超时时间
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        
    Returns:
        Optional[requests.Response]: 响应对象，失败返回None
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                params=data if method.upper() == 'GET' else None,
                timeout=timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                print(f"请求失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                print(f"请求最终失败: {e}")
                return None


def check_network(test_url: str = "https://www.baidu.com", timeout: int = 5) -> bool:
    """
    检查网络连接
    
    Args:
        test_url: 测试URL
        timeout: 超时时间
        
    Returns:
        bool: 网络可用返回True
    """
    try:
        response = requests.get(test_url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    """
    验证URL格式是否正确
    
    Args:
        url: 要验证的URL
        
    Returns:
        bool: URL格式正确返回True
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_domain_from_url(url: str) -> Optional[str]:
    """
    从URL中提取域名
    
    Args:
        url: URL字符串
        
    Returns:
        Optional[str]: 域名，失败返回None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def download_file(url: str, file_path: str, chunk_size: int = 8192,
                 progress_callback: Optional[callable] = None) -> bool:
    """
    下载文件
    
    Args:
        url: 文件URL
        file_path: 保存路径
        chunk_size: 块大小
        progress_callback: 进度回调函数
        
    Returns:
        bool: 下载成功返回True
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        progress_callback(progress)
        
        return True
        
    except Exception as e:
        print(f"下载文件失败: {e}")
        return False


def get_user_agent() -> str:
    """
    获取用户代理字符串
    
    Returns:
        str: 用户代理字符串
    """
    return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


def create_session_with_retries(max_retries: int = 3) -> requests.Session:
    """
    创建带重试机制的会话
    
    Args:
        max_retries: 最大重试次数
        
    Returns:
        requests.Session: 配置好的会话对象
    """
    session = requests.Session()
    
    # 设置重试策略
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置默认头部
    session.headers.update({
        'User-Agent': get_user_agent()
    })
    
    return session


__all__ = [
    "make_request",
    "check_network",
    "is_valid_url",
    "get_domain_from_url",
    "download_file",
    "get_user_agent",
    "create_session_with_retries"
]
