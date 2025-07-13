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

def generate_enhanced_epub(txt_file_path: str, output_dir: str, book_info: dict) -> bool:
    """
    生成带有详细信息和封面的增强版EPUB文件。
    
    Args:
        txt_file_path: TXT文件路径
        output_dir: 输出目录
        book_info: 书籍详细信息字典，包含:
            - book_name: 书名
            - author: 作者
            - description: 简介
            - thumb_url: 封面图片URL (可选)
            - read_count: 阅读量 (可选)
            - creation_status: 创作状态 (可选)
            - category_tags: 分类标签列表 (可选)
            - book_id: 书籍ID (可选)
            
    Returns:
        bool: 转换成功返回True，否则返回False
    """
    if not EBOOKLIB_AVAILABLE:
        print("错误: ebooklib 模块未安装，无法生成EPUB文件")
        return False
    
    try:
        # 提取书籍信息
        book_title = book_info.get('book_name', '未知书名')
        author = book_info.get('author', '未知作者')
        description = book_info.get('description', '')
        thumb_url = book_info.get('thumb_url')
        read_count = book_info.get('read_count')
        creation_status = book_info.get('creation_status')
        category_tags = book_info.get('category_tags', [])
        book_id = book_info.get('book_id', '')
        
        # 创建EPUB书籍对象
        book = epub.EpubBook()
        
        # 设置书籍元数据
        book.set_identifier(f'fanqie_{book_id}' if book_id else 'id123456')
        book.set_title(book_title)
        book.set_language('zh')
        book.add_author(author)
        
        if description:
            book.add_metadata('DC', 'description', description)
        
        # 添加出版商信息
        book.add_metadata('DC', 'publisher', '番茄小说')
        
        # 添加分类信息
        if category_tags:
            categories = [tag.get('category_name', '') for tag in category_tags if tag.get('category_name')]
            if categories:
                book.add_metadata('DC', 'subject', ' | '.join(categories))
        
        # 添加自定义元数据
        if read_count:
            book.add_metadata(None, 'meta', read_count, {'name': 'read_count', 'content': read_count})
        
        if creation_status:
            status_text = "完结" if creation_status == "1" else "连载中"
            book.add_metadata(None, 'meta', status_text, {'name': 'creation_status', 'content': status_text})
        
        # 下载并添加封面
        cover_added = False
        if thumb_url:
            try:
                import requests
                print("正在下载封面图片...")
                response = requests.get(thumb_url, timeout=10, stream=True)
                response.raise_for_status()
                
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'image' in content_type:
                    cover_data = response.content
                    
                    # 确定图片扩展名
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        cover_extension = '.jpg'
                        media_type = 'image/jpeg'
                    elif 'png' in content_type:
                        cover_extension = '.png'
                        media_type = 'image/png'
                    elif 'webp' in content_type:
                        cover_extension = '.webp'
                        media_type = 'image/webp'
                    else:
                        cover_extension = '.jpg'
                        media_type = 'image/jpeg'
                    
                    # 添加封面
                    book.set_cover(f"cover{cover_extension}", cover_data)
                    cover_added = True
                    print("封面下载并设置成功")
                else:
                    print(f"无效的图片类型: {content_type}")
                    
            except Exception as e:
                print(f"下载封面失败: {str(e)}")
        
        # 创建书籍信息页面
        info_content = _create_book_info_page(book_info, cover_added)
        info_chapter = epub.EpubHtml(title='书籍信息', file_name='book_info.xhtml', lang='zh')
        info_chapter.content = info_content
        book.add_item(info_chapter)
        
        # 读取并处理TXT文件内容（使用原有的处理逻辑）
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            print("错误: TXT文件为空，无法生成EPUB")
            return False
        
        # 分割章节（使用原有逻辑）
        chapters = _split_content_into_chapters(content)
        
        epub_chapters = []
        toc_entries = [info_chapter]  # 书籍信息页作为目录第一项
        
        for i, chapter_content in enumerate(chapters):
            if not chapter_content.strip():
                continue
                
            # 提取章节标题
            chapter_title, content_lines = _extract_chapter_title(chapter_content, i + 1)
            
            # 创建EPUB章节
            chapter_file_name = f'chapter_{i+1}.xhtml'
            epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='zh')
            
            # 格式化章节内容
            chapter_html = _create_chapter_html(chapter_title, content_lines)
            epub_chapter.content = chapter_html
            
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            toc_entries.append(epub_chapter)
        
        # 添加CSS样式
        _add_enhanced_css(book)
        
        # 设置目录
        book.toc = toc_entries
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 设置书脊（阅读顺序）
        book.spine = ['nav', info_chapter] + epub_chapters
        
        # 生成文件
        return _write_epub_file(book, book_title, output_dir)
        
    except Exception as e:
        print(f"生成增强版EPUB文件时出错: {e}")
        return False

def _create_book_info_page(book_info: dict, has_cover: bool) -> str:
    """创建书籍信息页面的HTML内容"""
    import html
    
    book_title = book_info.get('book_name', '未知书名')
    author = book_info.get('author', '未知作者')
    description = book_info.get('description', '暂无简介')
    read_count = book_info.get('read_count', '未知')
    creation_status = book_info.get('creation_status')
    category_tags = book_info.get('category_tags', [])
    book_id = book_info.get('book_id', '')
    
    status_text = "完结" if creation_status == "1" else "连载中" if creation_status == "0" else "未知"
    
    # 处理分类标签
    categories = []
    for tag in category_tags:
        if isinstance(tag, dict) and tag.get('category_name'):
            categories.append(tag['category_name'])
    category_text = ' | '.join(categories) if categories else '无分类信息'
    
    # 格式化简介
    description_paragraphs = []
    for para in description.split('\n'):
        para = para.strip()
        if para:
            description_paragraphs.append(f'<p>{html.escape(para)}</p>')
    
    cover_section = ''
    if has_cover:
        cover_section = '''
        <div class="cover-section">
            <img src="cover.jpg" alt="封面" class="cover-image" />
        </div>
        '''
    
    info_html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
    <title>书籍信息</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="content book-info">
        <h1>📚 书籍信息</h1>
        
        {cover_section}
        
        <div class="info-section">
            <h2>📖 《{html.escape(book_title)}》</h2>
            
            <div class="metadata">
                <p><strong>👤 作者:</strong> {html.escape(author)}</p>
                <p><strong>📊 状态:</strong> {status_text}</p>
                <p><strong>👀 阅读量:</strong> {html.escape(str(read_count))}</p>
                <p><strong>🏷️ 分类:</strong> {html.escape(category_text)}</p>
                {f'<p><strong>🆔 书籍ID:</strong> {html.escape(book_id)}</p>' if book_id else ''}
                <p><strong>📅 生成时间:</strong> {_get_current_datetime()}</p>
                <p><strong>📱 来源:</strong> 番茄小说</p>
            </div>
            
            <div class="description">
                <h3>📋 内容简介</h3>
                <div class="description-content">
                    {''.join(description_paragraphs) if description_paragraphs else '<p>暂无简介</p>'}
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    return info_html

def _split_content_into_chapters(content: str) -> list:
    """分割内容为章节（使用原有逻辑）"""
    import re
    
    chapter_patterns = [
        r'\n(?=第\s*[0-9]+\s*章)',
        r'\n(?=第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章)',
        r'\n(?=(?:番外|特别篇|外传|后记|序章|楔子|终章))',
        r'\n(?=Chapter\s+[0-9]+)',
        r'\n(?=第\s*[0-9]+\s*卷)',
    ]
    
    chapters = []
    content_to_split = content.strip()
    
    for pattern in chapter_patterns:
        try:
            temp_chapters = re.split(pattern, content_to_split, flags=re.MULTILINE | re.IGNORECASE)
            temp_chapters = [ch.strip() for ch in temp_chapters if ch.strip()]
            
            if len(temp_chapters) > 1:
                chapters = temp_chapters
                print(f"成功分割章节: {len(chapters)} 章")
                break
        except Exception:
            continue
    
    if not chapters or len(chapters) == 1:
        lines = content.split('\n')
        if len(lines) > 800:
            chapters = []
            lines_per_chapter = max(300, len(lines) // 20)
            for i in range(0, len(lines), lines_per_chapter):
                chapter_text = '\n'.join(lines[i:i+lines_per_chapter])
                if chapter_text.strip():
                    chapters.append(chapter_text)
        else:
            chapters = [content]
    
    return chapters

def _extract_chapter_title(chapter_content: str, chapter_num: int) -> tuple:
    """提取章节标题和内容"""
    import re
    
    lines = chapter_content.strip().split('\n')
    first_line = lines[0].strip() if lines else ""
    
    if re.match(r'^第\s*\d+\s*章|^第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章|^番外|^特别篇|^外传|^后记|^序章|^楔子|^终章', first_line, re.IGNORECASE):
        return first_line, lines[1:]
    elif re.match(r'.*第.*章.*|.*Chapter.*|.*卷.*', first_line, re.IGNORECASE):
        return first_line, lines[1:]
    else:
        return f"第{chapter_num}章", lines

def _create_chapter_html(chapter_title: str, content_lines: list) -> str:
    """创建章节HTML内容"""
    import html
    
    content_paragraphs = []
    for line in content_lines:
        line = line.strip()
        if line:
            escaped_line = html.escape(line, quote=True)
            escaped_line = escaped_line.replace('&quot;', '"')
            content_paragraphs.append(f'<p>{escaped_line}</p>')
    
    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
    <title>{html.escape(chapter_title, quote=True)}</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="content">
        <h1>{html.escape(chapter_title, quote=True)}</h1>
        {''.join(content_paragraphs) if content_paragraphs else '<p>本章节内容为空</p>'}
    </div>
</body>
</html>'''

def _add_enhanced_css(book):
    """添加增强的CSS样式"""
    style = '''
    @charset "utf-8";
    
    body { 
        font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "WenQuanYi Micro Hei", Arial, sans-serif; 
        line-height: 1.8; 
        margin: 20px; 
        padding: 0;
        background-color: #fefefe;
        color: #333;
    }
    
    h1 { 
        color: #2c3e50; 
        border-bottom: 2px solid #3498db; 
        padding-bottom: 10px; 
        margin-bottom: 20px;
        font-size: 1.5em;
        text-align: center;
    }
    
    h2 {
        color: #34495e;
        font-size: 1.3em;
        margin: 20px 0 15px 0;
        border-left: 4px solid #3498db;
        padding-left: 10px;
    }
    
    h3 {
        color: #34495e;
        font-size: 1.1em;
        margin: 15px 0 10px 0;
    }
    
    .content {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .book-info {
        padding: 20px;
    }
    
    .cover-section {
        text-align: center;
        margin: 20px 0;
    }
    
    .cover-image {
        max-width: 300px;
        max-height: 400px;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .info-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
    }
    
    .metadata {
        background: white;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
        border: 1px solid #e9ecef;
    }
    
    .metadata p {
        margin: 8px 0;
        text-indent: 0;
    }
    
    .description {
        margin: 20px 0;
    }
    
    .description-content {
        background: white;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #e9ecef;
    }
    
    p { 
        margin: 12px 0; 
        text-indent: 2em; 
        font-size: 1em;
        text-align: justify;
        word-wrap: break-word;
    }
    
    /* 移动端适配 */
    @media screen and (max-width: 600px) {
        body { margin: 10px; }
        h1 { font-size: 1.3em; }
        h2 { font-size: 1.2em; }
        p { font-size: 0.9em; }
        .cover-image { max-width: 200px; }
        .info-section { padding: 15px; }
    }
    '''
    
    nav_css = epub.EpubItem(uid="nav_css", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

def _write_epub_file(book, book_title: str, output_dir: str) -> bool:
    """写入EPUB文件"""
    try:
        safe_book_title = sanitize_filename(book_title)
        epub_file_path = os.path.join(output_dir, f"{safe_book_title}.epub")
        
        os.makedirs(output_dir, exist_ok=True)
        
        epub.write_epub(epub_file_path, book, {})
        
        if os.path.exists(epub_file_path) and os.path.getsize(epub_file_path) > 0:
            print(f"增强版EPUB文件已生成: {epub_file_path}")
            return True
        else:
            print("EPUB文件生成失败")
            return False
            
    except Exception as e:
        print(f"写入EPUB文件失败: {e}")
        return False

def _get_current_datetime() -> str:
    """获取当前时间字符串"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            content = f.read().strip()
        
        # 检查文件是否为空
        if not content:
            print("错误: TXT文件为空，无法生成EPUB")
            return False
        
        # 分割章节（改进的章节识别逻辑）
        import re
        
        # 定义多种章节模式，按优先级排序
        chapter_patterns = [
            # 标准章节模式：第X章
            r'\n(?=第\s*[0-9]+\s*章)',
            # 中文数字章节：第一章、第二章等
            r'\n(?=第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章)',
            # 特殊章节：番外、特别篇等
            r'\n(?=(?:番外|特别篇|外传|后记|序章|楔子|终章))',
            # 英文章节：Chapter
            r'\n(?=Chapter\s+[0-9]+)',
            # 卷+章节模式
            r'\n(?=第\s*[0-9]+\s*卷)',
            # 简单的章节模式（包含"章"字）
            r'\n(?=.*?章\s*[0-9]+)',
        ]
        
        chapters = []
        content_to_split = content.strip()
        
        # 尝试使用不同的章节模式进行分割
        for pattern in chapter_patterns:
            try:
                temp_chapters = re.split(pattern, content_to_split, flags=re.MULTILINE | re.IGNORECASE)
                # 过滤掉空章节
                temp_chapters = [ch.strip() for ch in temp_chapters if ch.strip()]
                
                # 如果分割出多个章节，使用这个结果
                if len(temp_chapters) > 1:
                    chapters = temp_chapters
                    print(f"成功使用模式分割章节: {pattern}, 章节数: {len(chapters)}")
                    break
            except Exception as e:
                print(f"章节分割模式 {pattern} 失败: {e}")
                continue
        
        # 如果所有模式都失败，使用智能分割
        if not chapters or len(chapters) == 1:
            lines = content.split('\n')
            # 对于长文本，按段落数量智能分割
            if len(lines) > 800:
                chapters = []
                lines_per_chapter = max(300, len(lines) // 20)  # 每章至少300行，最多20章
                for i in range(0, len(lines), lines_per_chapter):
                    chapter_text = '\n'.join(lines[i:i+lines_per_chapter])
                    if chapter_text.strip():
                        chapters.append(chapter_text)
                print(f"按行数智能分割: {len(chapters)} 章节")
            else:
                # 对于短文本，作为单章处理
                chapters = [content]
                print("内容较短，作为单章处理")
        
        epub_chapters = []
        toc_entries = []
        
        for i, chapter_content in enumerate(chapters):
            if not chapter_content.strip():
                continue
                
            # 提取章节标题（改进的标题提取）
            lines = chapter_content.strip().split('\n')
            first_line = lines[0].strip() if lines else ""
            
            # 智能识别章节标题
            chapter_title = ""
            if re.match(r'^第\s*\d+\s*章|^第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章|^番外|^特别篇|^外传|^后记|^序章|^楔子|^终章', first_line, re.IGNORECASE):
                chapter_title = first_line
                content_lines = lines[1:]  # 标题后的内容
            elif re.match(r'.*第.*章.*|.*Chapter.*|.*卷.*', first_line, re.IGNORECASE):
                chapter_title = first_line
                content_lines = lines[1:]
            else:
                chapter_title = f"第{i+1}章"
                content_lines = lines  # 没有明确标题，所有内容都是正文
            
            # 创建EPUB章节
            chapter_file_name = f'chapter_{i+1}.xhtml'
            epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='zh')
            
            # 格式化章节内容（改进的HTML生成和转义）
            import html
            content_paragraphs = []
            for line in content_lines:
                line = line.strip()
                if line:  # 非空行
                    # 使用标准HTML转义函数，处理所有特殊字符
                    escaped_line = html.escape(line, quote=True)
                    # 保留一些常见的格式符号
                    escaped_line = escaped_line.replace('&quot;', '"')  # 保留引号
                    content_paragraphs.append(f'<p>{escaped_line}</p>')
            
            # 改进的HTML结构，添加更好的元数据和样式
            chapter_html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
    <title>{html.escape(chapter_title, quote=True)}</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="content">
        <h1>{html.escape(chapter_title, quote=True)}</h1>
        {''.join(content_paragraphs) if content_paragraphs else '<p>本章节内容为空</p>'}
    </div>
</body>
</html>'''
            
            epub_chapter.content = chapter_html
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            toc_entries.append(epub_chapter)
        
        # 添加改进的CSS样式
        style = '''
        @charset "utf-8";
        
        body { 
            font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "WenQuanYi Micro Hei", Arial, sans-serif; 
            line-height: 1.8; 
            margin: 20px; 
            padding: 0;
            background-color: #fefefe;
            color: #333;
        }
        
        h1 { 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px; 
            margin-bottom: 20px;
            font-size: 1.5em;
            text-align: center;
        }
        
        .content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        p { 
            margin: 12px 0; 
            text-indent: 2em; 
            font-size: 1em;
            text-align: justify;
            word-wrap: break-word;
        }
        
        /* 移动端适配 */
        @media screen and (max-width: 600px) {
            body { margin: 10px; }
            h1 { font-size: 1.3em; }
            p { font-size: 0.9em; }
        }
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
        
        # 生成EPUB文件路径并确保目录存在
        try:
            safe_book_title = sanitize_filename(book_title)
            epub_file_path = os.path.join(output_dir, f"{safe_book_title}.epub")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 检查磁盘空间（粗略估算）
            import shutil
            free_space = shutil.disk_usage(output_dir).free
            if free_space < 10 * 1024 * 1024:  # 少于10MB
                print(f"警告: 磁盘空间可能不足，剩余空间: {free_space / 1024 / 1024:.1f}MB")
            
        except Exception as e:
            print(f"准备输出文件时出错: {e}")
            return False

        try:
            # 尝试标准写入方法
            epub.write_epub(epub_file_path, book, {})
            print(f"EPUB文件已生成: {epub_file_path}")
            
            # 验证生成的文件
            if os.path.exists(epub_file_path) and os.path.getsize(epub_file_path) > 0:
                print(f"EPUB文件验证成功，大小: {os.path.getsize(epub_file_path)} 字节")
                return True
            else:
                print("EPUB文件生成失败：文件不存在或为空")
                return False
                
        except Exception as write_error:
            print(f"标准方法写入EPUB失败: {write_error}")
            # 尝试备用方法
            try:
                print("尝试备用写入方法...")
                epub.write_epub(epub_file_path, book)
                
                # 再次验证文件
                if os.path.exists(epub_file_path) and os.path.getsize(epub_file_path) > 0:
                    print(f"EPUB文件已生成（备用方法）: {epub_file_path}")
                    return True
                else:
                    print("备用方法也失败了")
                    return False
                    
            except Exception as alt_error:
                print(f"备用方法也失败: {alt_error}")
                # 尝试清理可能损坏的文件
                try:
                    if os.path.exists(epub_file_path):
                        os.remove(epub_file_path)
                        print("已清理损坏的EPUB文件")
                except:
                    pass
                return False
        
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
        return "未命名文件"
    
    # 移除或替换不合法字符
    import re
    
    # Windows和Unix系统都不允许的字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 移除前后空格和点
    filename = filename.strip(' .')
    
    # 替换连续的下划线
    filename = re.sub(r'_{2,}', '_', filename)
    
    # 限制长度（考虑文件系统限制）
    max_length = 200
    if len(filename.encode('utf-8')) > max_length:
        # 按字节长度截断，确保不会截断UTF-8字符
        filename_bytes = filename.encode('utf-8')[:max_length]
        # 找到最后一个完整的UTF-8字符边界
        while filename_bytes:
            try:
                filename = filename_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                filename_bytes = filename_bytes[:-1]
    
    # 确保文件名不为空
    if not filename or filename == '_':
        filename = "未命名文件"
    
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
