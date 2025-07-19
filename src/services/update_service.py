"""
更新服务模块

负责检查和管理应用更新
"""

import requests
from packaging import version
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta

try:
    from ..config.constants import APP_VERSION
except ImportError:
    try:
        from config.constants import APP_VERSION
    except ImportError:
        APP_VERSION = "2.0.0"


class UpdateService:
    """更新服务类"""
    
    def __init__(self, repo_owner: str = "POf-L", repo_name: str = "Fanqie-novel-Downloader"):
        """
        初始化更新服务
        
        Args:
            repo_owner: GitHub仓库所有者
            repo_name: GitHub仓库名称
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        # 缓存相关
        self._last_check_time = None
        self._cached_result = None
        self._cache_duration = timedelta(hours=1)  # 缓存1小时
    
    def get_latest_version_info(self) -> Tuple[str, str, str]:
        """
        获取GitHub上的最新Release版本信息
        
        Returns:
            Tuple[str, str, str]: (tag_name, html_url, body)
        """
        headers = {"Accept": "application/vnd.github+json"}
        
        try:
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tag = data.get("tag_name", "")
            html_url = data.get("html_url", "")
            body = data.get("body", "")
            
            return tag, html_url, body
            
        except Exception as e:
            raise Exception(f"获取版本信息失败: {e}")
    
    def is_newer_version(self, remote_tag: str, local_ver: str = APP_VERSION) -> bool:
        """
        比较版本号，判断远程版本是否更新
        
        Args:
            remote_tag: 远程版本标签
            local_ver: 本地版本号
            
        Returns:
            bool: 远程版本更新返回True
        """
        # GitHub的tag通常以v开头，如v1.8
        remote_clean = remote_tag.lstrip("vV")
        
        try:
            return version.parse(remote_clean) > version.parse(local_ver)
        except Exception:
            # 解析失败时保守地返回False
            return False
    
    def check_for_updates(self, force_check: bool = False) -> Optional[Dict[str, Any]]:
        """
        检查是否有更新
        
        Args:
            force_check: 是否强制检查（忽略缓存）
            
        Returns:
            Optional[Dict]: 更新信息，如果没有更新则返回None
        """
        # 检查缓存
        if not force_check and self._is_cache_valid():
            return self._cached_result
        
        try:
            remote_tag, url, body = self.get_latest_version_info()
            
            update_info = None
            if remote_tag and self.is_newer_version(remote_tag):
                update_info = {
                    "has_update": True,
                    "latest_version": remote_tag,
                    "current_version": APP_VERSION,
                    "download_url": url,
                    "release_notes": body,
                    "check_time": datetime.now().isoformat()
                }
            else:
                update_info = {
                    "has_update": False,
                    "latest_version": remote_tag,
                    "current_version": APP_VERSION,
                    "check_time": datetime.now().isoformat()
                }
            
            # 更新缓存
            self._last_check_time = datetime.now()
            self._cached_result = update_info
            
            return update_info
            
        except Exception as e:
            # 检查失败时返回错误信息
            return {
                "has_update": False,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            }
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._last_check_time is None or self._cached_result is None:
            return False
        
        return datetime.now() - self._last_check_time < self._cache_duration
    
    def get_update_message(self, update_info: Dict[str, Any]) -> str:
        """
        生成更新消息
        
        Args:
            update_info: 更新信息
            
        Returns:
            str: 更新消息
        """
        if update_info.get("error"):
            return f"检查更新失败: {update_info['error']}"
        
        if not update_info.get("has_update"):
            return "当前已是最新版本"
        
        latest_version = update_info.get("latest_version", "未知")
        current_version = update_info.get("current_version", "未知")
        download_url = update_info.get("download_url", "")
        release_notes = update_info.get("release_notes", "")
        
        message_parts = [
            f"检测到新版本 {latest_version}（当前版本：{current_version}）"
        ]
        
        if release_notes:
            message_parts.append(f"\n更新内容:\n{release_notes}")
        
        if download_url:
            message_parts.append(f"\n请前往 {download_url} 下载更新")
        
        return "\n".join(message_parts)
    
    def clear_cache(self):
        """清除缓存"""
        self._last_check_time = None
        self._cached_result = None
    
    def set_cache_duration(self, hours: int):
        """
        设置缓存持续时间
        
        Args:
            hours: 缓存小时数
        """
        self._cache_duration = timedelta(hours=hours)
    
    def get_download_assets(self) -> list:
        """
        获取下载资源列表
        
        Returns:
            list: 下载资源信息列表
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            assets = data.get("assets", [])
            
            asset_list = []
            for asset in assets:
                asset_info = {
                    "name": asset.get("name", ""),
                    "size": asset.get("size", 0),
                    "download_count": asset.get("download_count", 0),
                    "download_url": asset.get("browser_download_url", ""),
                    "content_type": asset.get("content_type", "")
                }
                asset_list.append(asset_info)
            
            return asset_list
            
        except Exception as e:
            print(f"获取下载资源失败: {e}")
            return []
    
    def download_update(self, download_url: str, save_path: str, 
                       progress_callback: Optional[callable] = None) -> bool:
        """
        下载更新文件
        
        Args:
            download_url: 下载URL
            save_path: 保存路径
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载成功返回True
        """
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)
            
            return True
            
        except Exception as e:
            print(f"下载更新失败: {e}")
            return False


# 全局更新服务实例
_update_service = None


def get_update_service() -> UpdateService:
    """获取全局更新服务实例"""
    global _update_service
    if _update_service is None:
        _update_service = UpdateService()
    return _update_service


def check_update(force_check: bool = False) -> Optional[str]:
    """
    检查更新的便捷函数
    
    Args:
        force_check: 是否强制检查
        
    Returns:
        Optional[str]: 更新消息，如果没有更新则返回None
    """
    service = get_update_service()
    update_info = service.check_for_updates(force_check)
    
    if update_info and update_info.get("has_update"):
        return service.get_update_message(update_info)
    
    return None


__all__ = ["UpdateService", "get_update_service", "check_update"]
