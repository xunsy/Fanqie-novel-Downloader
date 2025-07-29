#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试所有模块导入
用于验证GitHub Actions中的依赖安装是否成功
"""

import sys
import traceback

def test_imports():
    """测试所有必需的模块导入"""
    
    # 需要测试的模块列表
    modules_to_test = [
        ('requests', 'requests'),
        ('PIL', 'Pillow'),
        ('PIL.Image', 'Pillow'),
        ('PIL.ImageTk', 'Pillow'),
        ('ebooklib', 'ebooklib'),
        ('bs4', 'beautifulsoup4'),
        ('fake_useragent', 'fake-useragent'),
        ('tqdm', 'tqdm'),
        ('urllib3', 'urllib3'),
    ]
    
    # 可选模块（如果安装失败不会影响主要功能）
    optional_modules = [
        ('pillow_heif', 'pillow-heif'),
    ]
    
    print("开始测试模块导入...")
    print("=" * 50)
    
    # 测试必需模块
    failed_modules = []
    for module_name, package_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} ({package_name}) - 导入成功")
        except ImportError as e:
            print(f"❌ {module_name} ({package_name}) - 导入失败: {e}")
            failed_modules.append((module_name, package_name))
        except Exception as e:
            print(f"⚠️ {module_name} ({package_name}) - 导入异常: {e}")
            failed_modules.append((module_name, package_name))
    
    print("\n" + "=" * 50)
    
    # 测试可选模块
    print("测试可选模块...")
    for module_name, package_name in optional_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name} ({package_name}) - 导入成功")
        except ImportError:
            print(f"⚠️ {module_name} ({package_name}) - 未安装（可选）")
        except Exception as e:
            print(f"⚠️ {module_name} ({package_name}) - 导入异常: {e}")
    
    print("\n" + "=" * 50)
    
    # 测试项目内部模块
    print("测试项目内部模块...")
    internal_modules = [
        'gui',
        'enhanced_downloader', 
        'tomato_novel_api',
        'updater',
        'version'
    ]
    
    for module_name in internal_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - 导入成功")
        except ImportError as e:
            print(f"❌ {module_name} - 导入失败: {e}")
            failed_modules.append((module_name, 'internal'))
        except Exception as e:
            print(f"⚠️ {module_name} - 导入异常: {e}")
            failed_modules.append((module_name, 'internal'))
    
    print("\n" + "=" * 50)
    
    # 输出结果
    if failed_modules:
        print("❌ 以下模块导入失败:")
        for module_name, package_name in failed_modules:
            print(f"  - {module_name} ({package_name})")
        print("\n请检查依赖安装是否正确。")
        return False
    else:
        print("✅ 所有必需模块导入成功！")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 