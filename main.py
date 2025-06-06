"""番茄小说下载器主程序入口"""

import os
import sys
import logging
import tempfile
import datetime

# 日志配置
log_file = os.path.join(tempfile.gettempdir(), f"fanqie_downloader_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.info("番茄小说下载器启动")
logging.info(f"Python版本: {sys.version}")
logging.info(f"运行路径: {os.getcwd()}")
logging.info(f"日志文件: {log_file}")

# 添加模块搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from gui import NovelDownloaderGUI
    from utils import center_window_on_screen
    from config import CONFIG
    import customtkinter as ctk
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有必需的依赖包")
    print("运行: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """程序主入口"""
    try:
        app = NovelDownloaderGUI()
        app.mainloop()
    except Exception as e:
        logging.exception(f"程序运行出错: {str(e)}")
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", f"程序运行出错: {str(e)}\n\n详细日志已保存到: {log_file}")
        root.destroy()
        raise

if __name__ == "__main__":
    try:
        logging.info("调用main()函数")
        main()
    except Exception as e:
        logging.exception(f"未捕获的异常: {str(e)}")
        print(f"程序出错! 详细日志已保存到: {log_file}")
        input("按Enter键退出...")