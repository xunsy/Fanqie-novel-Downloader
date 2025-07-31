#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python编译脚本
用于GitHub Actions中的可执行文件编译
"""

import subprocess
import sys
import os
import shutil

def build_executable():
    """编译可执行文件"""
    print("开始编译可执行文件...")
    
    # 检查build.spec文件
    if os.path.exists("build.spec"):
        print("使用build.spec配置文件编译")
        cmd = [sys.executable, "-m", "PyInstaller", "build.spec", "--clean", "--noconfirm"]
    else:
        print("未找到build.spec，使用默认配置编译")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--windowed",
            "--name=TomatoNovelDownloader",
            "--add-data=version.py" + (";" if os.name == "nt" else ":") + ".",
            "--hidden-import=bs4",
            "--hidden-import=beautifulsoup4",
            "--hidden-import=fake_useragent",
            "--hidden-import=tqdm",
            "--hidden-import=requests",
            "--hidden-import=urllib3",
            "--hidden-import=ebooklib",
            "--hidden-import=PIL",
            "--hidden-import=PIL.Image",
            "--hidden-import=PIL.ImageTk",
            "gui.py"
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("编译成功")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("编译失败")
        print(f"错误输出: {e.stderr}")
        return False

def check_output():
    """检查编译输出"""
    print("检查编译输出...")
    if os.path.exists("dist"):
        files = os.listdir("dist")
        print(f"dist目录内容: {files}")
        
        # 检查可执行文件
        exe_name = "TomatoNovelDownloader.exe" if os.name == "nt" else "TomatoNovelDownloader"
        exe_path = os.path.join("dist", exe_name)
        
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"可执行文件创建成功: {exe_name} ({size} bytes)")
            return True
        else:
            print(f"可执行文件不存在: {exe_path}")
            return False
    else:
        print("dist目录不存在")
        return False

def main():
    """主函数"""
    if build_executable():
        if check_output():
            print("编译完成！")
            return True
        else:
            print("编译输出检查失败")
            return False
    else:
        print("编译失败")
        return False

if __name__ == "__main__":
    main() 