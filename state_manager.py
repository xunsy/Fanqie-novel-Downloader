# -*- coding: utf-8 -*-
"""
状态管理模块
负责下载状态的保存和加载
"""

import os
import json
try:
    from config import CONFIG
except ImportError:
    CONFIG = {"status_file": "chapter.json"}


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        pass
    
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
            except Exception:
                return set()
        return set()
    
    def save_status(self, save_path, downloaded):
        """保存下载状态"""
        status_file = os.path.join(save_path, CONFIG["status_file"])
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(list(downloaded), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态失败: {str(e)}")
    
    def clear_status(self, save_path):
        """清除下载状态"""
        status_file = os.path.join(save_path, CONFIG["status_file"])
        if os.path.exists(status_file):
            try:
                os.remove(status_file)
            except Exception as e:
                print(f"清除状态失败: {str(e)}")
    
    def get_status_info(self, save_path):
        """获取状态信息"""
        downloaded = self.load_status(save_path)
        return {
            'downloaded_count': len(downloaded),
            'downloaded_chapters': list(downloaded)
        }