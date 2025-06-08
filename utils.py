"""
工具函数模块
包含项目中使用的各种工具函数
"""

import os
import sys
import tkinter as tk
from typing import Optional

# EPUB相关导入
try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，优先使用程序运行目录或可执行文件所在目录。
    确保配置文件等资源能够持久化保存，不会因为程序重启而丢失。

    Args:
        relative_path (str): 相对于程序目录的路径

    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # 优先使用可执行文件所在目录（适用于打包后的环境）
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            # PyInstaller打包环境：使用可执行文件所在目录
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境：使用脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        # 备用方案：使用当前工作目录
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def center_window_over_parent(child_window, parent_window):
    """
    将子窗口居中显示在父窗口上方。
    
    Args:
        child_window: 要居中的子窗口
        parent_window: 父窗口
    """
    try:
        # 更新窗口以获取准确的尺寸
        child_window.update_idletasks()
        parent_window.update_idletasks()
        
        # 获取父窗口的位置和尺寸
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        # 获取子窗口的尺寸
        child_width = child_window.winfo_reqwidth()
        child_height = child_window.winfo_reqheight()
        
        # 计算居中位置
        x = parent_x + (parent_width - child_width) // 2
        y = parent_y + (parent_height - child_height) // 2
        
        # 确保窗口不会超出屏幕边界
        screen_width = child_window.winfo_screenwidth()
        screen_height = child_window.winfo_screenheight()
        
        x = max(0, min(x, screen_width - child_width))
        y = max(0, min(y, screen_height - child_height))
        
        child_window.geometry(f"+{x}+{y}")
        
    except Exception as e:
        print(f"居中窗口时出错: {e}")

def center_window_on_screen(window, width: Optional[int] = None, height: Optional[int] = None):
    """
    将窗口居中显示在屏幕上。
    
    Args:
        window: 要居中的窗口
        width: 窗口宽度（可选）
        height: 窗口高度（可选）
    """
    try:
        window.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 获取窗口尺寸
        if width is None:
            width = window.winfo_reqwidth()
        if height is None:
            height = window.winfo_reqheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    except Exception as e:
        print(f"居中窗口时出错: {e}")

def generate_epub(txt_file_path: str, output_dir: str, book_title: str, author: str, description: str = "") -> bool:
    """
    将TXT文件转换为EPUB格式。
    
    Args:
        txt_file_path: TXT文件路径
        output_dir: 输出目录
        book_title: 书籍标题
        author: 作者
        description: 书籍描述
        
    Returns:
        bool: 转换成功返回True，否则返回False
    """
    if not EBOOKLIB_AVAILABLE:
        print("错误: ebooklib 模块未安装，无法生成EPUB文件")
        return False
    
    try:
        # 创建EPUB书籍对象
        book = epub.EpubBook()
        
        # 设置书籍元数据
        book.set_identifier('id123456')
        book.set_title(book_title)
        book.set_language('zh')
        book.add_author(author)
        if description:
            book.add_metadata('DC', 'description', description)
        
        # 读取TXT文件内容
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割章节（假设章节以"第X章"开头）
        import re
        chapters = re.split(r'\n(?=第\d+章|第[一二三四五六七八九十百千万]+章)', content)
        
        if not chapters or len(chapters) == 1:
            # 如果没有找到章节分割，将整个内容作为一章
            chapters = [content]
        
        epub_chapters = []
        toc_entries = []
        
        for i, chapter_content in enumerate(chapters):
            if not chapter_content.strip():
                continue
                
            # 提取章节标题
            lines = chapter_content.strip().split('\n')
            chapter_title = lines[0].strip() if lines else f"第{i+1}章"
            
            # 创建EPUB章节
            chapter_file_name = f'chapter_{i+1}.xhtml'
            epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='zh')
            
            # 格式化章节内容
            chapter_html = f"""
            <html>
            <head>
                <title>{chapter_title}</title>
            </head>
            <body>
                <h1>{chapter_title}</h1>
                <div>
                    {'<br/>'.join(line.strip() for line in lines[1:] if line.strip())}
                </div>
            </body>
            </html>
            """
            
            epub_chapter.content = chapter_html
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            toc_entries.append(epub_chapter)
        
        # 添加默认的CSS样式
        style = '''
        body { font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.6; margin: 20px; }
        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
        p { margin: 10px 0; text-indent: 2em; }
        '''
        nav_css = epub.EpubItem(uid="nav_css", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)
        
        # 设置目录
        book.toc = toc_entries
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 设置书脊（阅读顺序）
        book.spine = ['nav'] + epub_chapters
        
        # 生成EPUB文件
        epub_file_path = os.path.join(output_dir, f"{book_title}.epub")
        epub.write_epub(epub_file_path, book, {})
        
        print(f"EPUB文件已生成: {epub_file_path}")
        return True
        
    except Exception as e:
        print(f"生成EPUB文件时出错: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不合法字符。
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return ""
    
    # 移除或替换不合法字符
    import re
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 移除前后空格和点
    filename = filename.strip(' .')
    
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

# 导出的函数列表
__all__ = [
    'resource_path',
    'center_window_over_parent', 
    'center_window_on_screen',
    'generate_epub',
    'sanitize_filename',
    'EBOOKLIB_AVAILABLE'
]
