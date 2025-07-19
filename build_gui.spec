# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(os.path.abspath(SPECPATH)), 'src')
sys.path.insert(0, src_dir)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 包含src目录下的所有模块
        ('src', 'src'),
        # 包含requirements.txt
        ('requirements.txt', '.'),
        # 包含README.md
        ('README.md', '.'),
    ],
    hiddenimports=[
        # 确保所有模块都被包含
        'src.config.settings',
        'src.config.constants',
        'src.core.models.novel',
        'src.core.models.chapter',
        'src.core.downloaders.base',
        'src.core.downloaders.novel_downloader',
        'src.core.storage.file_manager',
        'src.services.update_service',
        'src.services.logging_service',
        'src.ui.main_window',
        'src.ui.components.download_panel',
        'src.ui.components.settings_panel',
        'src.ui.components.log_panel',
        'src.utils.file_utils',
        'src.utils.ui_utils',
        'src.utils.network_utils',
        'src.utils.format_converter',
        # CustomTkinter相关
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        # 网络相关
        'requests',
        'urllib3',
        'ssl',
        'certifi',
        # 其他依赖
        'packaging',
        'packaging.version',
        'json',
        'datetime',
        'threading',
        'concurrent.futures',
        'pathlib',
        'tempfile',
        'logging',
        'logging.handlers',
        # EPUB相关（可选）
        'ebooklib',
        'lxml',
        'html',
        # 平台相关
        'platformdirs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TomatoNovelDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)

# 如果是macOS，创建app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='TomatoNovelDownloader.app',
        icon=None,
        bundle_identifier='com.tomato.novel.downloader',
        info_plist={
            'CFBundleName': 'Tomato Novel Downloader',
            'CFBundleDisplayName': '番茄小说下载器',
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
