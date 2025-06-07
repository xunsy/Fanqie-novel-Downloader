# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

# 收集customtkinter的数据文件
customtkinter_datas = collect_data_files('customtkinter')

# 收集其他可能需要的数据文件
additional_datas = []

# 添加项目中的配置文件和资源（如果存在）
user_config_path = os.path.join(project_root, 'user_config.json')
if os.path.exists(user_config_path):
    additional_datas.append((user_config_path, '.'))

# 如果有assets目录，也包含进去
assets_dir = os.path.join(project_root, 'assets')
if os.path.exists(assets_dir):
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)
            additional_datas.append((file_path, os.path.dirname(rel_path)))

# 添加docs目录（如果存在）
docs_dir = os.path.join(project_root, 'docs')
if os.path.exists(docs_dir):
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(('.md', '.txt', '.js')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                additional_datas.append((file_path, os.path.dirname(rel_path)))

# 收集隐藏导入
hidden_imports = [
    'customtkinter',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'requests',
    'bs4',
    'beautifulsoup4',
    'tqdm',
    'stem',
    'stem.control',
    'fake_useragent',
    'Crypto',
    'Crypto.Cipher',
    'Crypto.Cipher.AES',
    'Crypto.Util.Padding',
    'Crypto.Random',
    'ebooklib',
    'ebooklib.epub',
    'urllib3',
    'json',
    'threading',
    'concurrent.futures',
    'collections',
    'typing',
    'base64',
    'gzip',
    'urllib.parse',
    'tempfile',
    'datetime',
    'logging',
    'os',
    'sys',
    're',
    'time',
    'random'
]

# 分析主程序
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=customtkinter_datas + additional_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 创建PYZ文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='番茄小说下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定路径
    version_file=None
)
