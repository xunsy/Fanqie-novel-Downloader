#!/usr/bin/env python3
"""
番茄小说下载器 - 命令行版本
提供无GUI的命令行下载功能
"""

from downloader import (
    enable_tor_support,
    fetch_api_endpoints_from_server,
    Run
)
import os



def main():
    """主函数"""
    print("番茄小说下载器 - 命令行版本")
    print("=" * 40)

    # 询问是否启用Tor
    use_tor = input("是否启用Tor代理? (y/N): ").strip().lower()
    if use_tor in ['y', 'yes']:
        if not enable_tor_support():
            print("将不使用Tor网络继续运行")

    print("正在从服务器获取API列表...")
    fetch_api_endpoints_from_server()

    while True:
        # 获取用户输入
        book_id = input("请输入小说ID（输入q退出）: ").strip()
        if book_id.lower() == 'q':
            break

        if not book_id:
            print("小说ID不能为空")
            continue

        save_path = input("请输入保存路径 (默认: downloads): ").strip()
        if not save_path:
            save_path = "downloads"

        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)

        print(f"开始下载小说 ID: {book_id}")
        print(f"保存路径: {save_path}")

        try:
            Run(book_id, save_path)
        except Exception as e:
            print(f"运行错误: {str(e)}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
