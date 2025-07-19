"""
常量定义模块

定义应用中使用的各种常量
"""

from typing import Dict, Any, List

# --- 应用信息 ---
APP_NAME = "TomatoNovelDownloader"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Tomato Novel Downloader Team"

# --- 默认窗口配置 ---
DEFAULT_WINDOW_CONFIG: Dict[str, Any] = {
    "default_geometry": "1300x850",
    "position": None,
    "min_width": 800,
    "min_height": 600
}

# --- 默认请求配置 ---
DEFAULT_REQUEST_CONFIG: Dict[str, Any] = {
    "max_workers": 4,
    "timeout": 15,
    "max_retries": 3,
    "request_rate_limit": 0.5,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- 默认下载配置 ---
DEFAULT_DOWNLOAD_CONFIG: Dict[str, Any] = {
    "mode": "batch",  # batch 或 single
    "batch_size": 50,
    "retry_count": 3,
    "retry_interval": 1.0,
    "auto_retry_failed": True,
    "save_format": "TXT",  # TXT, EPUB, BOTH
    "generate_epub_when_txt": False,
    "chapter_delay": 0.1  # 章节下载间隔（秒）
}

# --- 默认文件配置 ---
DEFAULT_FILE_CONFIG: Dict[str, str] = {
    "status_file_format": ".{book_id}.download_status",
    "default_save_path": "downloads",
    "last_save_path": "",
    "auto_create_author_folder": True,
    "filename_template": "{title}_{author}"
}

# --- 默认UI配置 ---
DEFAULT_UI_CONFIG: Dict[str, Any] = {
    "appearance_mode": "dark",
    "color_theme": "blue",
    "font_family": "Microsoft YaHei",
    "font_size": 12,
    "auto_save_settings": True,
    "show_progress_details": True,
    "enable_notifications": True
}

# --- 默认阅读器配置 ---
DEFAULT_READER_CONFIG: Dict[str, Any] = {
    "default_font": "Microsoft YaHei",
    "default_size": 14,
    "default_fg": "#DCE4EE",
    "default_bg": "#242424",
    "default_width": 1000,
    "default_height": 800,
    "padding": 10,
    "dark_mode": True,
    "auto_save_interval_ms": 30000
}

# --- 默认网络配置 ---
DEFAULT_NETWORK_CONFIG: Dict[str, Any] = {
    "enable_proxy": False,
    "proxy_type": "http",  # http, socks5
    "proxy_host": "",
    "proxy_port": 0,
    "proxy_username": "",
    "proxy_password": "",
    "verify_ssl": True,
    "connection_pool_size": 10
}

# --- 默认API配置 ---
DEFAULT_API_CONFIG: Dict[str, Any] = {
    "endpoints": [],
    "auth_token": "",
    "server_url": "https://dlbkltos.s7123.xyz:5080/api/sources",
    "timeout": 10,
    "max_retries": 3,
    "rate_limit": 0.5
}

# --- 默认批量下载配置 ---
DEFAULT_BATCH_CONFIG: Dict[str, Any] = {
    "name": "qyuing",
    "base_url": None,
    "batch_endpoint": None,
    "token": None,
    "max_batch_size": 290,
    "timeout": 10,
    "enabled": True,
    "concurrent_batches": 2
}

# --- Tor网络配置 ---
DEFAULT_TOR_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "proxy_port": 9050,
    "max_retries": 3,
    "change_ip_after": 980,
    "request_timeout": 35,
    "control_port": 9051,
    "control_password": ""
}

# --- 日志配置 ---
DEFAULT_LOG_CONFIG: Dict[str, Any] = {
    "level": "INFO",
    "enable_file_logging": True,
    "log_file_path": "",  # 空字符串表示使用默认路径
    "max_log_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "enable_console_logging": True
}

# --- 完整的默认配置 ---
DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR
    },
    "window": DEFAULT_WINDOW_CONFIG,
    "request": DEFAULT_REQUEST_CONFIG,
    "download": DEFAULT_DOWNLOAD_CONFIG,
    "file": DEFAULT_FILE_CONFIG,
    "ui": DEFAULT_UI_CONFIG,
    "reader": DEFAULT_READER_CONFIG,
    "network": DEFAULT_NETWORK_CONFIG,
    "api": DEFAULT_API_CONFIG,
    "batch": DEFAULT_BATCH_CONFIG,
    "tor": DEFAULT_TOR_CONFIG,
    "logging": DEFAULT_LOG_CONFIG
}

# --- 支持的输出格式 ---
SUPPORTED_OUTPUT_FORMATS: List[str] = ["TXT", "EPUB", "BOTH"]

# --- 支持的下载模式 ---
SUPPORTED_DOWNLOAD_MODES: List[str] = ["batch", "single"]

# --- 支持的主题 ---
SUPPORTED_THEMES: List[str] = ["blue", "green", "dark-blue"]

# --- 支持的外观模式 ---
SUPPORTED_APPEARANCE_MODES: List[str] = ["light", "dark", "system"]

# --- 文件扩展名 ---
FILE_EXTENSIONS: Dict[str, str] = {
    "TXT": ".txt",
    "EPUB": ".epub",
    "JSON": ".json",
    "LOG": ".log"
}

# --- 状态常量 ---
DOWNLOAD_STATUS = {
    "PENDING": "pending",
    "DOWNLOADING": "downloading", 
    "COMPLETED": "completed",
    "FAILED": "failed",
    "PAUSED": "paused",
    "CANCELLED": "cancelled"
}

CHAPTER_STATUS = {
    "PENDING": "pending",
    "DOWNLOADING": "downloading",
    "COMPLETED": "completed", 
    "FAILED": "failed"
}

# --- 错误代码 ---
ERROR_CODES = {
    "NETWORK_ERROR": 1001,
    "API_ERROR": 1002,
    "FILE_ERROR": 1003,
    "CONFIG_ERROR": 1004,
    "VALIDATION_ERROR": 1005,
    "UNKNOWN_ERROR": 9999
}

# --- API端点类型 ---
API_ENDPOINT_TYPES = {
    "NOVEL_INFO": "novel_info",
    "CHAPTER_LIST": "chapter_list", 
    "CHAPTER_CONTENT": "chapter_content",
    "BATCH_DOWNLOAD": "batch_download"
}

# --- 默认用户代理列表 ---
DEFAULT_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# --- 正则表达式模式 ---
REGEX_PATTERNS = {
    "CHAPTER_TITLE": [
        r'^第\s*\d+\s*章',
        r'^第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章',
        r'^番外|^特别篇|^外传|^后记|^序章|^楔子|^终章',
        r'.*第.*章.*|.*Chapter.*|.*卷.*'
    ],
    "BOOK_ID": r'^\d+$',
    "FILENAME_ILLEGAL_CHARS": r'[<>:"/\\|?*\x00-\x1f]'
}

# --- 限制常量 ---
LIMITS = {
    "MAX_FILENAME_LENGTH": 200,
    "MAX_CHAPTER_CONTENT_LENGTH": 1024 * 1024,  # 1MB
    "MAX_CONCURRENT_DOWNLOADS": 20,
    "MIN_REQUEST_INTERVAL": 0.1,
    "MAX_REQUEST_INTERVAL": 10.0,
    "MAX_RETRY_ATTEMPTS": 10
}


__all__ = [
    "APP_NAME", "APP_VERSION", "APP_AUTHOR",
    "DEFAULT_CONFIG",
    "SUPPORTED_OUTPUT_FORMATS", "SUPPORTED_DOWNLOAD_MODES",
    "SUPPORTED_THEMES", "SUPPORTED_APPEARANCE_MODES",
    "FILE_EXTENSIONS", "DOWNLOAD_STATUS", "CHAPTER_STATUS",
    "ERROR_CODES", "API_ENDPOINT_TYPES",
    "DEFAULT_USER_AGENTS", "REGEX_PATTERNS", "LIMITS"
]
