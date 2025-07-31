#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
番茄小说下载器 - 自动更新系统
"""

import requests
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import zipfile
import shutil
import subprocess
import tempfile
from typing import Dict, Optional
import platform


class AutoUpdater:
    def __init__(self, current_version: str = "1.0.0", repo_owner: str = "", repo_name: str = ""):
        self.current_version = current_version
        self.repo_owner = repo_owner or "POf-L"  # GitHub用户名
        self.repo_name = repo_name or "Fanqie-novel-Downloader"  # 仓库名
        self.github_api_base = "https://api.github.com"
        self.update_url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        
        # 检测当前平台
        self.platform = self._detect_platform()
        
        # 获取版本信息
        try:
            import version
            self.version_info = version.get_version_info()
            self.is_development = version.is_development_version()
        except ImportError:
            self.version_info = {
                'version': current_version,
                'is_compiled': False
            }
            self.is_development = False
        
    def _detect_platform(self) -> str:
        """检测当前运行平台"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "unknown"
    
    def check_for_updates(self) -> Optional[Dict]:
        """检查是否有新版本可用"""
        try:
            headers = {
                'User-Agent': 'TomatoNovelDownloader-Updater',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(self.update_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info['tag_name'].lstrip('v')
            
            print(f"[DEBUG] Checking for updates:")
            print(f"[DEBUG] Local version: {self.current_version}")
            print(f"[DEBUG] GitHub version: {latest_version}")
            print(f"[DEBUG] Is development version: {self.is_development}")
            print(f"[DEBUG] Version info: {self.version_info}")
            
            # 改进的版本比较逻辑
            should_update = self._should_update(latest_version, self.current_version)
            print(f"[DEBUG] Should update: {should_update}")
            
            if should_update:
                # 查找适合当前平台的下载链接
                download_url = self._find_platform_download(release_info['assets'])
                
                if download_url:
                    return {
                        'version': latest_version,
                        'download_url': download_url,
                        'changelog': release_info.get('body', ''),
                        'published_at': release_info.get('published_at', ''),
                        'name': release_info.get('name', f'v{latest_version}')
                    }
            
            return None
            
        except Exception as e:
            print(f"检查更新失败: {e}")
            return None
    
    def _should_update(self, latest: str, current: str) -> bool:
        """改进的更新检查逻辑"""
        try:
            # 先进行版本比较
            is_newer = self._is_newer_version(latest, current)
            
            if self.is_development:
                # 开发版本：只有当GitHub Release确实更新时才提示更新
                if is_newer:
                    print(f"[调试] 开发版本检测到更新的GitHub Release，建议更新")
                    return True
                else:
                    print(f"[调试] 开发版本已是最新或更新版本，无需更新")
                    return False
            else:
                # 编译版本：使用标准版本比较
                return is_newer
            
        except Exception as e:
            print(f"[调试] 版本比较异常: {e}")
            # 如果比较失败，假设有新版本（保守策略）
            return latest != current
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            # 简单的版本号比较，支持格式：YYYY.MM.DD.HHMM-xxxxxxx
            latest_parts = latest.split('-')[0].split('.')
            current_parts = current.split('-')[0].split('.')
            
            # 补齐版本号部分
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend(['0'] * (max_len - len(latest_parts)))
            current_parts.extend(['0'] * (max_len - len(current_parts)))
            
            for l, c in zip(latest_parts, current_parts):
                l_num = int(l)
                c_num = int(c)
                if l_num > c_num:
                    return True
                elif l_num < c_num:
                    return False
            
            # 如果版本号相同，比较提交哈希
            if '-' in latest and '-' in current:
                latest_hash = latest.split('-')[1]
                current_hash = current.split('-')[1]
                return latest_hash != current_hash
            
            return False
            
        except Exception:
            # 如果比较失败，假设有新版本
            return latest != current
    
    def _find_platform_download(self, assets: list) -> Optional[str]:
        """查找适合当前平台的下载链接"""
        for asset in assets:
            name = asset['name'].lower()
            if self.platform in name and name.endswith('.zip'):
                return asset['browser_download_url']
        return None
    
    def show_update_dialog(self, update_info: Dict) -> bool:
        """显示更新对话框"""
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        result = {'update': False}
        
        def create_dialog():
            dialog = tk.Toplevel()
            dialog.title("发现新版本")
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.grab_set()
            
            # 居中显示
            dialog.transient(root)
            
            # 标题
            title_label = tk.Label(dialog, text=f"🎉 发现新版本 {update_info['version']}", 
                                  font=('Microsoft YaHei', 14, 'bold'))
            title_label.pack(pady=20)
            
            # 信息框架
            info_frame = tk.Frame(dialog)
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # 版本信息
            version_info = f"当前版本: {self.current_version}\n新版本: {update_info['version']}\n发布时间: {update_info['published_at'][:10]}"
            version_label = tk.Label(info_frame, text=version_info, justify=tk.LEFT)
            version_label.pack(anchor='w', pady=(0, 10))
            
            # 更新日志
            tk.Label(info_frame, text="更新内容:", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
            
            changelog_frame = tk.Frame(info_frame)
            changelog_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 15))
            
            changelog_text = tk.Text(changelog_frame, wrap=tk.WORD, height=8)
            scrollbar = tk.Scrollbar(changelog_frame, orient=tk.VERTICAL, command=changelog_text.yview)
            changelog_text.configure(yscrollcommand=scrollbar.set)
            
            changelog_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            changelog_text.insert(tk.END, update_info['changelog'])
            changelog_text.config(state=tk.DISABLED)
            
            # 按钮框架
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=20, pady=20)
            
            def update_now():
                result['update'] = True
                dialog.destroy()
                root.quit()
            
            def skip_update():
                result['update'] = False
                dialog.destroy()
                root.quit()
            
            update_btn = tk.Button(button_frame, text="🚀 立即更新", 
                                 command=update_now, bg='#4CAF50', fg='white',
                                 font=('Microsoft YaHei', 10, 'bold'), padx=20)
            update_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            skip_btn = tk.Button(button_frame, text="❌ 跳过此版本", 
                               command=skip_update, bg='#f44336', fg='white',
                               font=('Microsoft YaHei', 10, 'bold'), padx=20)
            skip_btn.pack(side=tk.RIGHT)
            
            # 关闭窗口时的处理
            dialog.protocol("WM_DELETE_WINDOW", skip_update)
            
            # 运行对话框
            root.mainloop()
        
        create_dialog()
        root.destroy()
        
        return result['update']
    
    def download_and_install_update(self, update_info: Dict, progress_callback=None):
        """下载并安装更新"""
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            # 下载文件
            if progress_callback:
                progress_callback(10, "开始下载更新...")
            
            zip_path = os.path.join(temp_dir, "update.zip")
            self._download_file(update_info['download_url'], zip_path, progress_callback)
            
            if progress_callback:
                progress_callback(70, "解压更新文件...")
            
            # 解压文件
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            if progress_callback:
                progress_callback(90, "安装更新...")
            
            # 安装更新
            self._install_update(extract_dir)
            
            if progress_callback:
                progress_callback(100, "更新完成！")
            
            return True
            
        except Exception as e:
            print(f"更新失败: {e}")
            if progress_callback:
                progress_callback(-1, f"更新失败: {str(e)}")
            return False
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _download_file(self, url: str, filepath: str, progress_callback=None):
        """下载文件"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = 10 + (downloaded / total_size) * 60  # 10-70%
                        progress_callback(progress, f"下载中... {downloaded/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB")
    
    def _install_update(self, extract_dir: str):
        """安装更新"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 查找解压目录中的可执行文件或Python文件
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(('.exe', '.py')) and 'gui' in file.lower():
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(current_dir, file)
                    
                    # 备份原文件
                    if os.path.exists(dst_path):
                        backup_path = dst_path + '.backup'
                        shutil.copy2(dst_path, backup_path)
                    
                    # 复制新文件
                    shutil.copy2(src_path, dst_path)
                    
                    # 如果是可执行文件，给予执行权限
                    if file.endswith('.exe') and os.name != 'nt':
                        os.chmod(dst_path, 0o755)
    
    def check_and_update_async(self, force_check=False):
        """异步检查并更新"""
        def update_thread():
            # 检查更新
            update_info = self.check_for_updates()
            
            if update_info:
                # 显示更新对话框
                if self.show_update_dialog(update_info):
                    # 创建进度窗口
                    self._show_progress_window(update_info)
            elif force_check:
                # 如果是手动检查，显示"已是最新版本"
                messagebox.showinfo("检查更新", "当前已是最新版本！")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def _show_progress_window(self, update_info: Dict):
        """显示更新进度窗口"""
        root = tk.Tk()
        root.title("正在更新...")
        root.geometry("400x200")
        root.resizable(False, False)
        
        # 居中显示
        root.eval('tk::PlaceWindow . center')
        
        # 进度标签
        progress_label = tk.Label(root, text="准备下载更新...", font=('Microsoft YaHei', 10))
        progress_label.pack(pady=20)
        
        # 进度条
        progress_bar = ttk.Progressbar(root, mode='determinate', length=300)
        progress_bar.pack(pady=10)
        
        # 状态标签
        status_label = tk.Label(root, text="", font=('Microsoft YaHei', 9), fg='gray')
        status_label.pack(pady=5)
        
        def progress_callback(progress, message):
            if progress >= 0:
                progress_bar['value'] = progress
            progress_label.config(text=message)
            root.update()
            
            if progress == 100:
                # 更新完成，重启应用
                root.after(2000, lambda: self._restart_application(root))
        
        # 在新线程中执行更新
        def update_thread():
            success = self.download_and_install_update(update_info, progress_callback)
            if not success:
                root.after(0, lambda: messagebox.showerror("更新失败", "更新过程中出现错误"))
                root.after(0, root.destroy)
        
        threading.Thread(target=update_thread, daemon=True).start()
        root.mainloop()
    
    def _restart_application(self, window):
        """重启应用程序"""
        window.destroy()
        
        # 显示重启提示
        restart_root = tk.Tk()
        restart_root.withdraw()
        
        if messagebox.askyesno("更新完成", "更新已完成！是否立即重启应用程序？"):
            # 重启应用
            if getattr(sys, 'frozen', False):
                # 如果是打包的可执行文件
                os.execl(sys.executable, sys.executable)
            else:
                # 如果是Python脚本
                os.execl(sys.executable, sys.executable, *sys.argv)
        
        restart_root.destroy()


def get_current_version():
    """获取当前版本号"""
    try:
        # 尝试从version.py获取版本信息
        import version
        return version.VERSION
    except ImportError:
        # 如果没有version.py，返回默认版本
        return "1.0.0"


if __name__ == "__main__":
    # 测试更新器
    current_ver = get_current_version()
    updater = AutoUpdater(current_ver)
    
    print(f"当前版本: {current_ver}")
    print("检查更新...")
    
    update_info = updater.check_for_updates()
    if update_info:
        print(f"发现新版本: {update_info['version']}")
        print(f"下载链接: {update_info['download_url']}")
    else:
        print("当前已是最新版本")