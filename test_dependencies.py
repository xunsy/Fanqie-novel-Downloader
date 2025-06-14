#!/usr/bin/env python3
"""
依赖测试脚本
用于验证所有必需的依赖包是否正确安装
"""

import sys
import importlib
from typing import List, Tuple

def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    测试模块导入
    
    Args:
        module_name: 要导入的模块名
        package_name: 包名（用于显示）
    
    Returns:
        (是否成功, 错误信息)
    """
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)

def main():
    """主测试函数"""
    print("🔍 开始检查依赖包...")
    print("=" * 50)
    
    # 定义要测试的依赖包
    dependencies = [
        # 标准库
        ("tkinter", "tkinter (Python标准库)"),
        ("json", "json (Python标准库)"),
        ("os", "os (Python标准库)"),
        ("sys", "sys (Python标准库)"),
        ("threading", "threading (Python标准库)"),
        
        # 第三方包
        ("customtkinter", "customtkinter"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("tqdm", "tqdm"),
        ("fake_useragent", "fake-useragent"),
        ("ebooklib", "ebooklib"),
        ("stem", "stem"),
        ("Crypto", "pycryptodome"),
        ("platformdirs", "platformdirs"),
        ("typing_extensions", "typing-extensions"),
        ("chardet", "chardet"),
        ("lxml", "lxml"),
        ("urllib3", "urllib3"),
    ]
    
    success_count = 0
    failed_packages = []
    
    for module_name, display_name in dependencies:
        success, error = test_import(module_name)
        
        if success:
            print(f"✅ {display_name}")
            success_count += 1
        else:
            print(f"❌ {display_name} - {error}")
            failed_packages.append((display_name, error))
    
    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{len(dependencies)} 个包可用")
    
    if failed_packages:
        print("\n❌ 失败的包:")
        for package, error in failed_packages:
            print(f"   - {package}: {error}")
        
        print("\n🔧 解决建议:")
        if any("tkinter" in pkg[0] for pkg in failed_packages):
            print("   - tkinter问题: 请参考 TKINTER_SETUP.md")
        
        print("   - 其他包问题: 运行 'pip install -r requirements.txt'")
        print("   - CI环境: 使用 'pip install -r requirements-ci.txt'")
        
        return 1
    else:
        print("\n🎉 所有依赖包都已正确安装!")
        
        # 额外测试：尝试创建GUI窗口
        try:
            print("\n🖥️ 测试GUI功能...")
            import tkinter as tk
            import customtkinter as ctk
            
            # 创建测试窗口（不显示）
            root = ctk.CTk()
            root.withdraw()  # 隐藏窗口
            root.destroy()
            
            print("✅ GUI功能测试通过")
        except Exception as e:
            print(f"⚠️ GUI功能测试失败: {e}")
            print("   这可能是因为运行在无显示环境中（如CI）")
        
        return 0

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n🚀 环境检查完成，可以运行程序了!")
        print("   - GUI版本: python main.py")
        print("   - 命令行版本: python cli.py")
    else:
        print("\n⚠️ 请解决上述依赖问题后再运行程序")
    
    sys.exit(exit_code)
