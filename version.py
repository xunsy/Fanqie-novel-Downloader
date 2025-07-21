# -*- coding: utf-8 -*-
"""
版本信息文件
注意：实际版本号由GitHub Actions自动生成，此文件仅作为fallback
"""

VERSION = "dev-local"  # 开发版本标识
BUILD_TIME = "local"
COMMIT_HASH = "development"
BRANCH = "main"

def get_version_info():
    """获取完整版本信息"""
    return {
        'version': VERSION,
        'build_time': BUILD_TIME,
        'commit_hash': COMMIT_HASH,
        'branch': BRANCH
    }

def get_version_string():
    """获取版本字符串"""
    return f"v{VERSION}"

if __name__ == '__main__':
    print(f"版本: {VERSION}")
    print(f"构建时间: {BUILD_TIME}")
    print(f"提交哈希: {COMMIT_HASH}")
    print(f"分支: {BRANCH}")
