# -*- coding: utf-8 -*-
"""
网络请求模块
统一处理HTTP请求、请求头生成和API端点管理
"""

import requests
import random
import time
import json
from typing import Dict, List, Optional, Any
from fake_useragent import UserAgent
from config import Config


class NetworkManager:
    """网络请求管理器"""
    
    def __init__(self):
        self.config = Config()
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def get_headers(self) -> Dict[str, str]:
        """生成随机请求头"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        return headers
    
    def make_request(self, url: str, headers: Optional[Dict[str, str]] = None, 
                    params: Optional[Dict[str, Any]] = None, 
                    data: Optional[Dict[str, Any]] = None, 
                    method: str = 'GET', 
                    timeout: Optional[int] = None) -> Optional[requests.Response]:
        """
        统一的HTTP请求方法
        
        Args:
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: POST数据
            method: 请求方法
            timeout: 超时时间
            
        Returns:
            Response对象或None
        """
        if headers is None:
            headers = self.get_headers()
            
        if timeout is None:
            timeout = self.config.REQUEST_TIMEOUT
            
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(
                        url, 
                        headers=headers, 
                        params=params, 
                        timeout=timeout
                    )
                elif method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        headers=headers, 
                        params=params, 
                        data=data, 
                        timeout=timeout
                    )
                else:
                    response = self.session.request(
                        method, 
                        url, 
                        headers=headers, 
                        params=params, 
                        data=data, 
                        timeout=timeout
                    )
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{self.config.MAX_RETRIES}): {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    print(f"请求最终失败: {url}")
                    return None
                    
        return None
    
    def fetch_api_endpoints_from_server(self) -> List[str]:
        """从服务器获取API端点列表"""
        try:
            headers = self.get_headers()
            headers.update({
                'Authorization': f'Bearer {self.config.AUTH_TOKEN}',
                'Content-Type': 'application/json'
            })
            
            response = self.make_request(
                self.config.SERVER_URL,
                headers=headers,
                timeout=10
            )
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'endpoints' in data:
                        endpoints = data['endpoints']
                        if isinstance(endpoints, list):
                            print(f"从服务器获取到 {len(endpoints)} 个API端点")
                            return endpoints
                    elif isinstance(data, list):
                        print(f"从服务器获取到 {len(data)} 个API端点")
                        return data
                except json.JSONDecodeError:
                    print("服务器响应不是有效的JSON格式")
            else:
                print(f"服务器响应异常: {response.status_code if response else 'None'}")
                
        except Exception as e:
            print(f"获取API端点时发生错误: {e}")
            
        # 返回空列表，让主程序处理
        print("使用默认API端点")
        return []
    
    def get_api_endpoints(self) -> List[str]:
        """获取API端点列表（优先从服务器获取，失败则使用默认）"""
        if not self.config.API_ENDPOINTS:
            self.config.API_ENDPOINTS = self.fetch_api_endpoints_from_server()
        return self.config.API_ENDPOINTS
    
    def test_endpoint(self, endpoint: str) -> bool:
        """测试API端点是否可用"""
        try:
            response = self.make_request(endpoint, timeout=5)
            return response is not None and response.status_code == 200
        except:
            return False
    
    def get_working_endpoints(self) -> List[str]:
        """获取可用的API端点"""
        endpoints = self.get_api_endpoints()
        working_endpoints = []
        
        for endpoint in endpoints:
            if self.test_endpoint(endpoint):
                working_endpoints.append(endpoint)
                
        return working_endpoints if working_endpoints else endpoints
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()