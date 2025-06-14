# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - GUI版本
用于编译独立的、无控制台窗口的番茄小说下载器
"""

import os
from PyInstaller.utils.hooks import collect_data_files

# 收集customtkinter数据文件
customtkinter_datas = collect_data_files('customtkinter')

# 分析主程序
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=customtkinter_datas,
    hiddenimports=[
        'platformdirs',  # 确保包含此库
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'requests',
        'bs4',
        'beautifulsoup4',
        'tqdm',
        'stem',
        'fake_useragent',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'ebooklib',
        'ebooklib.epub',
        'urllib3',
        'lxml',
        'lxml.etree',
        'lxml.html',
        'PySocks',
        'socks',
        'json',
        'threading',
        'concurrent.futures',
        'collections',
        'datetime',
        'time',
        'os',
        'sys',
        'traceback'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'sklearn'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 创建PYZ归档
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TomatoNovelDownloader', # 设置发布名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关闭控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 未找到图标，可在此处添加路径
)
