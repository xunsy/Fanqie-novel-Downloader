"""
日志服务模块

提供统一的日志管理功能
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile

try:
    from ..config.constants import DEFAULT_LOG_CONFIG, APP_NAME
except ImportError:
    try:
        from config.constants import DEFAULT_LOG_CONFIG, APP_NAME
    except ImportError:
        DEFAULT_LOG_CONFIG = {
            'level': 'INFO',
            'enable_file_logging': True,
            'enable_console_logging': True,
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'max_log_size': 10 * 1024 * 1024,
            'backup_count': 5
        }
        APP_NAME = "TomatoNovelDownloader"


class LoggingService:
    """日志服务类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志服务
        
        Args:
            config: 日志配置
        """
        self.config = config or DEFAULT_LOG_CONFIG.copy()
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.get('level', 'INFO')))
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式器
        formatter = logging.Formatter(
            self.config.get('log_format', DEFAULT_LOG_CONFIG['log_format'])
        )
        
        # 设置控制台日志
        if self.config.get('enable_console_logging', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 设置文件日志
        if self.config.get('enable_file_logging', True):
            log_file_path = self._get_log_file_path()
            
            # 使用RotatingFileHandler支持日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=self.config.get('max_log_size', 10 * 1024 * 1024),
                backupCount=self.config.get('backup_count', 5),
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def _get_log_file_path(self) -> str:
        """获取日志文件路径"""
        log_file_path = self.config.get('log_file_path', '')
        
        if not log_file_path:
            # 使用默认路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"{APP_NAME}_{timestamp}.log"
            log_file_path = os.path.join(tempfile.gettempdir(), log_filename)
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)
        
        return log_file_path
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            logging.Logger: 日志器实例
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def log(self, level: str, message: str, logger_name: str = "main"):
        """
        记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            logger_name: 日志器名称
        """
        logger = self.get_logger(logger_name)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)
    
    def debug(self, message: str, logger_name: str = "main"):
        """记录调试日志"""
        self.log("debug", message, logger_name)
    
    def info(self, message: str, logger_name: str = "main"):
        """记录信息日志"""
        self.log("info", message, logger_name)
    
    def warning(self, message: str, logger_name: str = "main"):
        """记录警告日志"""
        self.log("warning", message, logger_name)
    
    def error(self, message: str, logger_name: str = "main"):
        """记录错误日志"""
        self.log("error", message, logger_name)
    
    def critical(self, message: str, logger_name: str = "main"):
        """记录严重错误日志"""
        self.log("critical", message, logger_name)
    
    def exception(self, message: str, logger_name: str = "main"):
        """记录异常日志（包含堆栈跟踪）"""
        logger = self.get_logger(logger_name)
        logger.exception(message)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        self.config['level'] = level.upper()
    
    def add_file_handler(self, file_path: str, level: str = "INFO"):
        """
        添加文件处理器
        
        Args:
            file_path: 文件路径
            level: 日志级别
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # 设置格式器
        formatter = logging.Formatter(self.config.get('log_format'))
        file_handler.setFormatter(formatter)
        
        # 添加到根日志器
        logging.getLogger().addHandler(file_handler)
    
    def remove_file_handlers(self):
        """移除所有文件处理器"""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
                root_logger.removeHandler(handler)
                handler.close()
    
    def get_log_files(self) -> list:
        """
        获取日志文件列表
        
        Returns:
            list: 日志文件路径列表
        """
        log_files = []
        
        # 获取当前日志文件路径
        current_log_file = self._get_log_file_path()
        log_dir = os.path.dirname(current_log_file)
        
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log') and APP_NAME in file:
                    log_files.append(os.path.join(log_dir, file))
        
        return sorted(log_files, key=os.path.getmtime, reverse=True)
    
    def clear_old_logs(self, keep_days: int = 7):
        """
        清理旧日志文件
        
        Args:
            keep_days: 保留天数
        """
        import time
        
        log_files = self.get_log_files()
        current_time = time.time()
        
        for log_file in log_files:
            try:
                file_time = os.path.getmtime(log_file)
                if current_time - file_time > keep_days * 24 * 3600:
                    os.remove(log_file)
                    self.info(f"删除旧日志文件: {log_file}")
            except Exception as e:
                self.error(f"删除日志文件失败 {log_file}: {e}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Returns:
            Dict: 日志统计信息
        """
        log_files = self.get_log_files()
        total_size = 0
        
        for log_file in log_files:
            try:
                total_size += os.path.getsize(log_file)
            except Exception:
                continue
        
        return {
            "total_files": len(log_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "current_level": self.config.get('level', 'INFO'),
            "file_logging_enabled": self.config.get('enable_file_logging', True),
            "console_logging_enabled": self.config.get('enable_console_logging', True)
        }
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新日志配置
        
        Args:
            config: 新的配置
        """
        self.config.update(config)
        self._setup_logging()


# 全局日志服务实例
_logging_service = None


def get_logging_service() -> LoggingService:
    """获取全局日志服务实例"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service


def get_logger(name: str = "main") -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    service = get_logging_service()
    return service.get_logger(name)


# 便捷的日志函数
def log_debug(message: str, logger_name: str = "main"):
    """记录调试日志"""
    get_logging_service().debug(message, logger_name)


def log_info(message: str, logger_name: str = "main"):
    """记录信息日志"""
    get_logging_service().info(message, logger_name)


def log_warning(message: str, logger_name: str = "main"):
    """记录警告日志"""
    get_logging_service().warning(message, logger_name)


def log_error(message: str, logger_name: str = "main"):
    """记录错误日志"""
    get_logging_service().error(message, logger_name)


def log_exception(message: str, logger_name: str = "main"):
    """记录异常日志"""
    get_logging_service().exception(message, logger_name)


__all__ = [
    "LoggingService",
    "get_logging_service",
    "get_logger",
    "log_debug", "log_info", "log_warning", "log_error", "log_exception"
]
