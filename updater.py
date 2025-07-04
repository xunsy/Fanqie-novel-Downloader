"""
GitHub 更新检查器
使用 GitHub Releases API 检查是否有新版本可用。
"""
from __future__ import annotations

import requests
from packaging import version
from typing import Tuple, Optional

from version import __version__

REPO_OWNER = "POf-L"
REPO_NAME = "Fanqie-novel-Downloader"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

def get_latest_version() -> Tuple[str, str]:
    """获取 GitHub 上的最新 Release 版本号和下载地址

    Returns
    -------
    Tuple[str, str]
        (tag_name, html_url)
    """
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(API_URL, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    tag = data.get("tag_name", "")
    html_url = data.get("html_url", data.get("assets", [{}])[0].get("browser_download_url", ""))
    return tag, html_url

def is_newer(remote_tag: str, local_ver: str = __version__) -> bool:
    """比较版本号，判断远程版本是否更新

    GitHub 的 tag 通常以 v 开头，如 v1.8
    """
    remote_clean = remote_tag.lstrip("vV")
    try:
        return version.parse(remote_clean) > version.parse(local_ver)
    except Exception:
        # 解析失败时保守地返回 False
        return False

def check_update() -> Optional[str]:
    """检查是否有更新，返回更新地址或 None"""
    try:
        remote_tag, url = get_latest_version()
        if remote_tag and is_newer(remote_tag):
            return f"检测到新版本 {remote_tag}，请前往 {url} 下载更新。"
    except Exception as e:
        # 记录错误但不影响主流程
        print(f"检查更新失败: {e}")
    return None

if __name__ == "__main__":
    msg = check_update()
    if msg:
        print(msg)
    else:
        print("当前已是最新版本。")
