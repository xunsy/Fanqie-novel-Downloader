# -*- coding: utf-8 -*-
# 版本信息文件 - 支持GitHub Actions动态生成

import os
import subprocess
from datetime import datetime

# 默认版本信息（本地开发时使用）
DEFAULT_VERSION = "2024.07.25.1900"
DEFAULT_BUILD_TIME = "2024.07.25.1900"
DEFAULT_COMMIT_HASH = "local-dev"
DEFAULT_BRANCH = "main"

def get_git_info():
    """获取Git信息"""
    try:
        # 获取commit hash
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                            stderr=subprocess.DEVNULL).decode().strip()[:7]
        
        # 获取分支名
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                       stderr=subprocess.DEVNULL).decode().strip()
        
        # 生成时间戳版本号
        timestamp = datetime.now().strftime("%Y.%m.%d.%H%M")
        version = f"{timestamp}-{commit_hash}"
        
        return {
            'version': version,
            'build_time': timestamp,
            'commit_hash': commit_hash,
            'branch': branch
        }
    except:
        return None

# 优先从环境变量获取（GitHub Actions设置），其次从Git获取，最后使用默认值
VERSION = os.getenv('VERSION') or (get_git_info() or {}).get('version', DEFAULT_VERSION)
BUILD_TIME = os.getenv('BUILD_TIME') or (get_git_info() or {}).get('build_time', DEFAULT_BUILD_TIME)
COMMIT_HASH = os.getenv('COMMIT_HASH') or (get_git_info() or {}).get('commit_hash', DEFAULT_COMMIT_HASH)
BRANCH = os.getenv('BRANCH') or (get_git_info() or {}).get('branch', DEFAULT_BRANCH)

def get_version_info():
    return {
        'version': VERSION,
        'build_time': BUILD_TIME,
        'commit_hash': COMMIT_HASH,
        'branch': BRANCH
    }

def get_version_string():
    return f"v{VERSION}"