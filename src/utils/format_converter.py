"""
格式转换工具模块

包含TXT到EPUB等格式转换功能
"""

import os
import re
import html
import datetime
from typing import List, Dict, Any, Optional, Tuple

# EPUB相关导入
try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

try:
    from .file_utils import sanitize_filename, ensure_directory_exists, check_disk_space
except ImportError:
    try:
        from file_utils import sanitize_filename, ensure_directory_exists, check_disk_space
    except ImportError:
        # 提供基础实现
        import os
        import re
        def sanitize_filename(name):
            return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
        def ensure_directory_exists(path):
            os.makedirs(path, exist_ok=True)
        def check_disk_space(path, required=0):
            return True


class EpubConverter:
    """EPUB转换器类"""
    
    def __init__(self):
        self.chapter_patterns = [
            r'\n(?=第\s*[0-9]+\s*章)',
            r'\n(?=第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章)',
            r'\n(?=(?:番外|特别篇|外传|后记|序章|楔子|终章))',
            r'\n(?=Chapter\s+[0-9]+)',
            r'\n(?=第\s*[0-9]+\s*卷)',
        ]
    
    def convert_txt_to_epub(self, txt_file_path: str, output_dir: str, 
                           book_title: str, author: str, description: str = "") -> bool:
        """
        将TXT文件转换为EPUB格式
        
        Args:
            txt_file_path: TXT文件路径
            output_dir: 输出目录
            book_title: 书籍标题
            author: 作者
            description: 书籍描述
            
        Returns:
            bool: 转换成功返回True
        """
        if not EBOOKLIB_AVAILABLE:
            print("错误: ebooklib 模块未安装，无法生成EPUB文件")
            return False
        
        try:
            # 读取TXT文件
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割章节
            chapters = self._split_content_into_chapters(content)
            
            # 创建EPUB书籍
            book = epub.EpubBook()
            book.set_identifier(f'novel_{hash(book_title)}')
            book.set_title(book_title)
            book.set_language('zh')
            book.add_author(author)
            
            if description:
                book.add_metadata('DC', 'description', description)
            
            # 添加CSS样式
            self._add_basic_css(book)
            
            # 处理章节
            epub_chapters = []
            toc_entries = []
            
            for i, chapter_content in enumerate(chapters):
                if not chapter_content.strip():
                    continue
                
                # 提取章节标题和内容
                chapter_title, content_lines = self._extract_chapter_title(chapter_content, i + 1)
                
                # 创建EPUB章节
                chapter_html = self._create_chapter_html(chapter_title, content_lines)
                chapter_file = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{i+1}.xhtml',
                    lang='zh'
                )
                chapter_file.content = chapter_html
                
                book.add_item(chapter_file)
                epub_chapters.append(chapter_file)
                toc_entries.append(epub.Link(f'chapter_{i+1}.xhtml', chapter_title, f'chapter_{i+1}'))
            
            # 设置目录和导航
            book.toc = toc_entries
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav'] + epub_chapters
            
            # 生成文件
            return self._write_epub_file(book, book_title, output_dir)
            
        except Exception as e:
            print(f"转换EPUB文件时出错: {e}")
            return False
    
    def convert_enhanced_epub(self, txt_file_path: str, output_dir: str, book_info: Dict[str, Any]) -> bool:
        """
        生成带有详细信息的增强版EPUB文件
        
        Args:
            txt_file_path: TXT文件路径
            output_dir: 输出目录
            book_info: 书籍详细信息字典
            
        Returns:
            bool: 转换成功返回True
        """
        if not EBOOKLIB_AVAILABLE:
            print("错误: ebooklib 模块未安装，无法生成EPUB文件")
            return False
        
        try:
            # 提取书籍信息
            book_title = book_info.get('book_name', '未知书名')
            author = book_info.get('author', '未知作者')
            description = book_info.get('description', '')
            
            # 读取TXT文件
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建EPUB书籍
            book = epub.EpubBook()
            book.set_identifier(f'novel_{hash(book_title)}')
            book.set_title(book_title)
            book.set_language('zh')
            book.add_author(author)
            
            # 添加详细元数据
            self._add_enhanced_metadata(book, book_info)
            
            # 添加增强CSS样式
            self._add_enhanced_css(book)
            
            # 创建信息页面
            info_chapter = self._create_info_chapter(book_info)
            book.add_item(info_chapter)
            
            # 处理正文章节
            chapters = self._split_content_into_chapters(content)
            epub_chapters = []
            toc_entries = [epub.Link('info.xhtml', '📖 书籍信息', 'info')]
            
            for i, chapter_content in enumerate(chapters):
                if not chapter_content.strip():
                    continue
                
                chapter_title, content_lines = self._extract_chapter_title(chapter_content, i + 1)
                chapter_html = self._create_enhanced_chapter_html(chapter_title, content_lines)
                
                chapter_file = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{i+1}.xhtml',
                    lang='zh'
                )
                chapter_file.content = chapter_html
                
                book.add_item(chapter_file)
                epub_chapters.append(chapter_file)
                toc_entries.append(epub.Link(f'chapter_{i+1}.xhtml', chapter_title, f'chapter_{i+1}'))
            
            # 设置目录和导航
            book.toc = toc_entries
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav', info_chapter] + epub_chapters
            
            return self._write_epub_file(book, book_title, output_dir)
            
        except Exception as e:
            print(f"生成增强版EPUB文件时出错: {e}")
            return False
    
    def _split_content_into_chapters(self, content: str) -> List[str]:
        """分割内容为章节"""
        chapters = []
        content_to_split = content.strip()
        
        # 尝试使用不同的章节模式进行分割
        for pattern in self.chapter_patterns:
            try:
                temp_chapters = re.split(pattern, content_to_split, flags=re.MULTILINE | re.IGNORECASE)
                temp_chapters = [ch.strip() for ch in temp_chapters if ch.strip()]
                
                if len(temp_chapters) > 1:
                    chapters = temp_chapters
                    print(f"成功分割章节: {len(chapters)} 章")
                    break
            except Exception:
                continue
        
        # 如果所有模式都失败，使用智能分割
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
    
    def _extract_chapter_title(self, chapter_content: str, chapter_num: int) -> Tuple[str, List[str]]:
        """提取章节标题和内容"""
        lines = chapter_content.strip().split('\n')
        first_line = lines[0].strip() if lines else ""
        
        title_patterns = [
            r'^第\s*\d+\s*章',
            r'^第\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\s*章',
            r'^番外|^特别篇|^外传|^后记|^序章|^楔子|^终章',
            r'.*第.*章.*|.*Chapter.*|.*卷.*'
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                return first_line, lines[1:]
        
        return f"第{chapter_num}章", lines


    def _create_chapter_html(self, chapter_title: str, content_lines: List[str]) -> str:
        """创建章节HTML内容"""
        content_paragraphs = []
        for line in content_lines:
            line = line.strip()
            if line:
                content_paragraphs.append(f'<p>{html.escape(line)}</p>')

        return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
    <title>{html.escape(chapter_title)}</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="content">
        <h1>{html.escape(chapter_title)}</h1>
        {''.join(content_paragraphs) if content_paragraphs else '<p>本章节内容为空</p>'}
    </div>
</body>
</html>'''

    def _create_enhanced_chapter_html(self, chapter_title: str, content_lines: List[str]) -> str:
        """创建增强版章节HTML内容"""
        return self._create_chapter_html(chapter_title, content_lines)

    def _add_basic_css(self, book):
        """添加基础CSS样式"""
        style = '''
        body { font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.6; margin: 20px; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        p { margin-bottom: 15px; text-indent: 2em; }
        .content { max-width: 800px; margin: 0 auto; }
        '''
        nav_css = epub.EpubItem(uid="nav_css", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)

    def _add_enhanced_css(self, book):
        """添加增强版CSS样式"""
        style = '''
        body { font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.8; margin: 0; padding: 20px; background: #fafafa; }
        .content { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 1.8em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; margin-bottom: 20px; }
        h3 { color: #7f8c8d; margin-top: 25px; margin-bottom: 15px; }
        p { margin-bottom: 15px; text-indent: 2em; color: #2c3e50; }
        .info-section { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .metadata p { text-indent: 0; margin: 8px 0; }
        .description-content { background: white; padding: 15px; border-radius: 5px; margin-top: 10px; }
        '''
        nav_css = epub.EpubItem(uid="nav_css", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)

    def _add_enhanced_metadata(self, book, book_info: Dict[str, Any]):
        """添加增强版元数据"""
        # 基础元数据
        if book_info.get('description'):
            book.add_metadata('DC', 'description', book_info['description'])

        book.add_metadata('DC', 'publisher', '番茄小说')

        # 分类信息
        category_tags = book_info.get('category_tags', [])
        if category_tags:
            categories = []
            for tag in category_tags:
                if isinstance(tag, dict) and tag.get('category_name'):
                    categories.append(tag['category_name'])
                elif isinstance(tag, str):
                    categories.append(tag)
            if categories:
                book.add_metadata('DC', 'subject', ' | '.join(categories))

        # 自定义元数据
        if book_info.get('read_count'):
            book.add_metadata(None, 'meta', str(book_info['read_count']),
                            {'name': 'read_count', 'content': str(book_info['read_count'])})

        if book_info.get('creation_status'):
            status_text = "完结" if book_info['creation_status'] == "0" else "连载中"
            book.add_metadata(None, 'meta', status_text,
                            {'name': 'creation_status', 'content': status_text})

    def _create_info_chapter(self, book_info: Dict[str, Any]):
        """创建书籍信息页面"""
        book_title = book_info.get('book_name', '未知书名')
        author = book_info.get('author', '未知作者')
        description = book_info.get('description', '暂无简介')

        # 处理其他信息
        read_count = book_info.get('read_count', '未知')
        creation_status = book_info.get('creation_status', '未知')
        status_text = "完结" if creation_status == "0" else "连载中" if creation_status else "未知"

        category_tags = book_info.get('category_tags', [])
        category_text = "未分类"
        if category_tags:
            categories = []
            for tag in category_tags:
                if isinstance(tag, dict) and tag.get('category_name'):
                    categories.append(tag['category_name'])
                elif isinstance(tag, str):
                    categories.append(tag)
            if categories:
                category_text = ' | '.join(categories)

        book_id = book_info.get('book_id', '')
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 处理简介段落
        description_paragraphs = []
        if description:
            for para in description.split('\n'):
                para = para.strip()
                if para:
                    description_paragraphs.append(f'<p>{html.escape(para)}</p>')

        info_html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
    <title>📖 书籍信息</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="content">
        <div class="info-section">
            <h2>📖 《{html.escape(book_title)}》</h2>
            <div class="metadata">
                <p><strong>👤 作者:</strong> {html.escape(author)}</p>
                <p><strong>📊 状态:</strong> {status_text}</p>
                <p><strong>👀 阅读量:</strong> {html.escape(str(read_count))}</p>
                <p><strong>🏷️ 分类:</strong> {html.escape(category_text)}</p>
                {f'<p><strong>🆔 书籍ID:</strong> {html.escape(book_id)}</p>' if book_id else ''}
                <p><strong>📅 生成时间:</strong> {current_time}</p>
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

        info_chapter = epub.EpubHtml(title='📖 书籍信息', file_name='info.xhtml', lang='zh')
        info_chapter.content = info_html
        return info_chapter

    def _write_epub_file(self, book, book_title: str, output_dir: str) -> bool:
        """写入EPUB文件"""
        try:
            safe_book_title = sanitize_filename(book_title)
            epub_file_path = os.path.join(output_dir, f"{safe_book_title}.epub")

            # 确保输出目录存在
            ensure_directory_exists(output_dir)

            # 检查磁盘空间
            if not check_disk_space(output_dir):
                print("警告: 磁盘空间可能不足")

            # 写入EPUB文件
            epub.write_epub(epub_file_path, book, {})
            print(f"✅ EPUB文件生成成功: {epub_file_path}")
            return True

        except Exception as e:
            print(f"写入EPUB文件失败: {e}")
            return False


# 便捷函数
def generate_epub(txt_file_path: str, output_dir: str, book_title: str,
                 author: str, description: str = "") -> bool:
    """
    便捷函数：将TXT文件转换为EPUB格式
    """
    converter = EpubConverter()
    return converter.convert_txt_to_epub(txt_file_path, output_dir, book_title, author, description)


def generate_enhanced_epub(txt_file_path: str, output_dir: str, book_info: Dict[str, Any]) -> bool:
    """
    便捷函数：生成增强版EPUB文件
    """
    converter = EpubConverter()
    return converter.convert_enhanced_epub(txt_file_path, output_dir, book_info)


__all__ = ["EpubConverter", "EBOOKLIB_AVAILABLE", "generate_epub", "generate_enhanced_epub"]
