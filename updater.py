#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新模块
检查GitHub Releases的最新版本并提供更新功能
"""

import requests
import json
import os
import sys
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class AutoUpdater:
    def __init__(self, current_version=None, repo_url=""):
        self.current_version = current_version or self.get_current_version()
        self.repo_url = repo_url.rstrip('/')

        # 处理不同格式的repo_url
        if repo_url.startswith('https://github.com/'):
            # 完整URL格式: https://github.com/POf-L/Fanqie-novel-Downloader
            repo_path = repo_url.replace('https://github.com/', '')
        else:
            # 简短格式: POf-L/Fanqie-novel-Downloader
            repo_path = repo_url

        self.api_base = f"https://api.github.com/repos/{repo_path}"
        # 不使用GitHub Pages，直接使用GitHub API
        self.latest_info_url = None
        
    def get_current_version(self):
        """获取当前版本号 - 优先从GitHub获取，fallback到本地"""
        try:
            # 首先尝试从GitHub获取当前运行版本的tag
            # 这样确保版本号与发布版本完全一致
            response = requests.get(f"{self.api_base}/releases", timeout=5)
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    # 获取最新的release作为当前版本
                    latest_release = releases[0]
                    return latest_release['tag_name'].replace('v', '')
        except:
            pass

        # Fallback到本地版本文件
        try:
            import version
            return version.VERSION
        except ImportError:
            return "0.0.0.0000"
    
    def check_for_updates(self):
        """检查是否有新版本"""
        try:
            # 直接从GitHub Releases API获取最新版本
            response = requests.get(f"{self.api_base}/releases/latest", timeout=10)
            if response.status_code == 200:
                release_info = response.json()
                latest_version = release_info['tag_name'].replace('v', '')

                if self.is_newer_version(latest_version, self.current_version):
                    # 查找下载链接
                    download_url = None
                    for asset in release_info.get('assets', []):
                        if asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            break

                    # 获取git提交日志作为更新日志
                    changelog = self.get_git_changelog(latest_version)

                    return {
                        'has_update': True,
                        'latest_version': latest_version,
                        'download_url': download_url,
                        'changelog_url': release_info.get('html_url'),
                        'update_time': release_info.get('published_at'),
                        'changelog': changelog,
                        'release_notes': release_info.get('body', '')
                    }

            return {'has_update': False}

        except Exception as e:
            print(f"检查更新失败: {str(e)}")
            return {'has_update': False, 'error': str(e)}

    def get_git_changelog(self, version):
        """获取git提交日志作为更新日志"""
        try:
            # 获取当前版本到最新版本之间的提交
            commits_url = f"{self.api_base}/commits"
            response = requests.get(commits_url, params={'per_page': 10}, timeout=10)

            if response.status_code == 200:
                commits = response.json()
                changelog_lines = []

                for commit in commits[:5]:  # 只显示最近5个提交
                    message = commit['commit']['message'].split('\n')[0]  # 只取第一行
                    author = commit['commit']['author']['name']
                    date = commit['commit']['author']['date'][:10]  # 只取日期部分

                    changelog_lines.append(f"• {message} ({author}, {date})")

                return '\n'.join(changelog_lines)

        except Exception as e:
            print(f"获取git日志失败: {str(e)}")

        return "• 基于最新代码自动构建\n• 修复已知问题和Bug\n• 性能优化和改进"
    
    def is_newer_version(self, latest, current):
        """比较版本号"""
        try:
            # 版本格式: 2025.01.21.1152-abc1234
            latest_parts = latest.split('-')[0].split('.')
            current_parts = current.split('-')[0].split('.')
            
            # 补齐到4位
            while len(latest_parts) < 4:
                latest_parts.append('0')
            while len(current_parts) < 4:
                current_parts.append('0')
            
            for i in range(4):
                latest_num = int(latest_parts[i])
                current_num = int(current_parts[i])
                
                if latest_num > current_num:
                    return True
                elif latest_num < current_num:
                    return False
            
            return False
        except:
            return latest != current
    
    def download_update(self, download_url, progress_callback=None):
        """下载更新文件"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'update.zip')
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            return temp_file
            
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")
    
    def install_update(self, zip_file_path):
        """安装更新"""
        try:
            # 获取当前程序目录
            current_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
            
            # 创建备份目录
            backup_dir = current_dir / 'backup'
            backup_dir.mkdir(exist_ok=True)
            
            # 解压更新文件
            temp_extract_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # 查找可执行文件
            exe_files = list(Path(temp_extract_dir).rglob('*.exe'))
            if not exe_files:
                raise Exception("更新包中未找到可执行文件")
            
            new_exe = exe_files[0]
            current_exe = Path(sys.executable) if getattr(sys, 'frozen', False) else Path('GUI.py')
            
            # 备份当前版本
            if current_exe.exists():
                backup_file = backup_dir / f"{current_exe.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{current_exe.suffix}"
                shutil.copy2(current_exe, backup_file)
            
            # 创建更新脚本
            update_script = current_dir / 'update.bat'
            script_content = f'''@echo off
echo 正在更新程序...
timeout /t 2 /nobreak >nul
copy /Y "{new_exe}" "{current_exe}"
echo 更新完成！
start "" "{current_exe}"
del "%~f0"
'''
            
            with open(update_script, 'w', encoding='gbk') as f:
                f.write(script_content)
            
            # 启动更新脚本并退出当前程序
            subprocess.Popen([str(update_script)], shell=True)
            return True
            
        except Exception as e:
            raise Exception(f"安装更新失败: {str(e)}")

class UpdateDialog:
    def __init__(self, parent, update_info):
        self.update_info = update_info
        self.result = False
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("发现新版本")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self.create_widgets()
        
    def create_widgets(self):
        # 标题
        title_frame = tk.Frame(self.dialog, bg='#f0f0f0', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🚀 发现新版本", 
                              font=('Microsoft YaHei', 16, 'bold'),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(expand=True)
        
        # 版本信息
        info_frame = tk.Frame(self.dialog, padx=20, pady=20)
        info_frame.pack(fill='both', expand=True)
        
        # 版本对比
        version_frame = tk.Frame(info_frame)
        version_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(version_frame, text="当前版本:", font=('Microsoft YaHei', 10)).pack(anchor='w')
        tk.Label(version_frame, text=AutoUpdater().current_version, 
                font=('Consolas', 10), fg='#666').pack(anchor='w', padx=(20, 0))
        
        tk.Label(version_frame, text="最新版本:", font=('Microsoft YaHei', 10)).pack(anchor='w', pady=(10, 0))
        tk.Label(version_frame, text=self.update_info['latest_version'], 
                font=('Consolas', 10), fg='#e74c3c').pack(anchor='w', padx=(20, 0))
        
        # 更新说明
        tk.Label(info_frame, text="更新说明:", font=('Microsoft YaHei', 10)).pack(anchor='w', pady=(15, 5))
        
        changelog_text = tk.Text(info_frame, height=8, wrap='word', 
                               font=('Microsoft YaHei', 9), bg='#f8f9fa')
        changelog_text.pack(fill='both', expand=True, pady=(0, 15))
        
        # 构建更新日志内容
        update_time = self.update_info.get('update_time', '未知')
        if update_time != '未知' and 'T' in update_time:
            update_time = update_time.split('T')[0]  # 只显示日期部分

        changelog_content = f"""版本: {self.update_info['latest_version']}
更新时间: {update_time}

最近提交记录:
{self.update_info.get('changelog', '• 基于最新代码自动构建')}

Release说明:
{self.update_info.get('release_notes', '详细更新内容请查看GitHub Release页面')}

建议立即更新以获得最佳体验！"""
        
        changelog_text.insert('1.0', changelog_content)
        changelog_text.config(state='disabled')
        
        # 按钮
        button_frame = tk.Frame(info_frame)
        button_frame.pack(fill='x')
        
        update_btn = tk.Button(button_frame, text="立即更新", 
                              command=self.start_update,
                              bg='#3498db', fg='white', 
                              font=('Microsoft YaHei', 10),
                              padx=20, pady=5)
        update_btn.pack(side='right', padx=(10, 0))
        
        later_btn = tk.Button(button_frame, text="稍后更新", 
                             command=self.close_dialog,
                             font=('Microsoft YaHei', 10),
                             padx=20, pady=5)
        later_btn.pack(side='right')
        
    def start_update(self):
        self.result = True
        self.dialog.destroy()
        
    def close_dialog(self):
        self.result = False
        self.dialog.destroy()

def check_and_update(parent_window=None, repo_url=""):
    """检查并处理更新"""
    updater = AutoUpdater(repo_url=repo_url)
    
    try:
        update_info = updater.check_for_updates()
        
        if update_info.get('has_update'):
            # 显示更新对话框
            if parent_window:
                dialog = UpdateDialog(parent_window, update_info)
                parent_window.wait_window(dialog.dialog)
                
                if dialog.result:
                    # 用户选择更新
                    progress_window = create_progress_window(parent_window)
                    
                    def update_progress(progress):
                        progress_window['progress'].set(progress)
                        progress_window['window'].update()
                    
                    try:
                        # 下载更新
                        zip_file = updater.download_update(
                            update_info['download_url'], 
                            update_progress
                        )
                        
                        progress_window['window'].destroy()
                        
                        # 安装更新
                        if updater.install_update(zip_file):
                            messagebox.showinfo("更新完成", "程序将重启以完成更新")
                            sys.exit(0)
                        
                    except Exception as e:
                        progress_window['window'].destroy()
                        messagebox.showerror("更新失败", f"更新过程中出现错误:\n{str(e)}")
            else:
                print(f"发现新版本: {update_info['latest_version']}")
                return update_info
        else:
            if parent_window:
                messagebox.showinfo("检查更新", "当前已是最新版本")
            else:
                print("当前已是最新版本")
                
    except Exception as e:
        if parent_window:
            messagebox.showerror("检查更新失败", f"无法检查更新:\n{str(e)}")
        else:
            print(f"检查更新失败: {str(e)}")

def create_progress_window(parent):
    """创建进度窗口"""
    window = tk.Toplevel(parent)
    window.title("正在更新")
    window.geometry("400x150")
    window.resizable(False, False)
    window.transient(parent)
    window.grab_set()
    
    # 居中
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (400 // 2)
    y = (window.winfo_screenheight() // 2) - (150 // 2)
    window.geometry(f"400x150+{x}+{y}")
    
    tk.Label(window, text="正在下载更新...", 
            font=('Microsoft YaHei', 12)).pack(pady=20)
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(window, variable=progress_var, 
                                  maximum=100, length=300)
    progress_bar.pack(pady=10)
    
    return {'window': window, 'progress': progress_var}

if __name__ == '__main__':
    # 测试更新功能
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    check_and_update(repo_url="POf-L/Fanqie-novel-Downloader")
    
    root.destroy()
