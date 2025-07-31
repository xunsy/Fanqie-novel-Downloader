# -*- coding: utf-8 -*-
"""
文件输出模块
处理TXT和EPUB文件的生成和保存
"""

import os
import time
from ebooklib import epub


class FileOutputManager:
    """文件输出管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def log(self, message):
        """日志输出"""
        if self.logger:
            self.logger(message)
        else:
            print(message)
    
    def save_as_txt(self, filepath, book_data, chapters, chapter_results):
        """保存为TXT文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入书籍信息
                f.write(f"书名: {book_data.get('name', '未知书名')}\n")
                f.write(f"作者: {book_data.get('author', '未知作者')}\n")
                f.write(f"简介: {book_data.get('description', '无简介')}\n")
                f.write("=" * 50 + "\n\n")
                
                # 写入章节内容
                for idx in range(len(chapters)):
                    if idx in chapter_results:
                        result = chapter_results[idx]
                        title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                        f.write(f'{title}\n')
                        f.write(result['content'] + '\n\n')
            
            self.log(f"TXT文件保存成功: {filepath}")
            return True
        except Exception as e:
            self.log(f"保存TXT文件失败: {str(e)}")
            return False
    
    def save_as_epub(self, filepath, book_data, chapters, chapter_results):
        """保存为EPUB文件"""
        try:
            book = self.create_epub_book(book_data, chapters, chapter_results)
            epub.write_epub(filepath, book, {})
            self.log(f"EPUB文件保存成功: {filepath}")
            return True
        except Exception as e:
            self.log(f"保存EPUB文件失败: {str(e)}")
            return False
    
    def create_epub_book(self, book_data, chapters, chapter_results):
        """创建EPUB书籍对象"""
        book = epub.EpubBook()
        
        # 设置书籍元数据
        book.set_identifier(f'book_{book_data.get("name", "unknown")}_{int(time.time())}')
        book.set_title(book_data.get('name', '未知书名'))
        book.set_language('zh-CN')
        book.add_author(book_data.get('author', '未知作者'))
        book.add_metadata('DC', 'description', book_data.get('description', '无简介'))
        
        book.toc = []
        spine = ['nav']
        
        # 添加章节
        for idx in range(len(chapters)):
            if idx in chapter_results:
                result = chapter_results[idx]
                title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chap_{idx}.xhtml',
                    lang='zh-CN'
                )
                
                content = result['content'].replace('\n', '<br/>')
                chapter.content = f'<h1>{title}</h1><p>{content}</p>'.encode('utf-8')
                
                book.add_item(chapter)
                book.toc.append(chapter)
                spine.append(chapter)
        
        # 添加导航
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        
        return book
    
    def create_epub_with_enhanced_info(self, filepath, enhanced_info, chapters, chapter_results):
        """使用增强信息创建EPUB文件"""
        try:
            book = epub.EpubBook()
            
            # 设置书籍元数据
            book.set_identifier(f'book_{enhanced_info.get("book_id", "unknown")}_{int(time.time())}')
            book.set_title(enhanced_info.get('book_name', '未知书名'))
            book.set_language('zh-CN')
            book.add_author(enhanced_info.get('author', '未知作者'))
            book.add_metadata('DC', 'description', enhanced_info.get('abstract', '无简介'))
            
            # 添加更多元数据
            if enhanced_info.get('category'):
                book.add_metadata('DC', 'subject', enhanced_info['category'])
            if enhanced_info.get('tags'):
                book.add_metadata('DC', 'subject', enhanced_info['tags'])
            if enhanced_info.get('creation_status') == '0':
                book.add_metadata('DC', 'type', '完结')
            else:
                book.add_metadata('DC', 'type', '连载中')
            
            book.toc = []
            spine = ['nav']
            
            # 添加书籍信息页
            info_chapter = epub.EpubHtml(
                title='书籍信息',
                file_name='book_info.xhtml',
                lang='zh-CN'
            )
            
            info_content = f"""
            <h1>书籍信息</h1>
            <p><strong>书名:</strong> {enhanced_info.get('book_name', '未知书名')}</p>
            <p><strong>作者:</strong> {enhanced_info.get('author', '未知作者')}</p>
            <p><strong>分类:</strong> {enhanced_info.get('category', '未知分类')}</p>
            <p><strong>标签:</strong> {enhanced_info.get('tags', '无标签')}</p>
            <p><strong>评分:</strong> {enhanced_info.get('score', '0')}</p>
            <p><strong>字数:</strong> {enhanced_info.get('word_number', '0')}</p>
            <p><strong>章节数:</strong> {enhanced_info.get('serial_count', '0')}</p>
            <p><strong>状态:</strong> {'完结' if enhanced_info.get('creation_status') == '0' else '连载中'}</p>
            <p><strong>阅读量:</strong> {enhanced_info.get('read_count', '0')}</p>
            <p><strong>简介:</strong></p>
            <p>{enhanced_info.get('abstract', '无简介')}</p>
            """
            
            info_chapter.content = info_content.encode('utf-8')
            book.add_item(info_chapter)
            book.toc.append(info_chapter)
            spine.append(info_chapter)
            
            # 添加章节内容
            for idx in range(len(chapters)):
                if idx in chapter_results:
                    result = chapter_results[idx]
                    title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                    
                    chapter = epub.EpubHtml(
                        title=title,
                        file_name=f'chap_{idx}.xhtml',
                        lang='zh-CN'
                    )
                    
                    content = result['content'].replace('\n', '<br/>')
                    chapter.content = f'<h1>{title}</h1><p>{content}</p>'.encode('utf-8')
                    
                    book.add_item(chapter)
                    book.toc.append(chapter)
                    spine.append(chapter)
            
            # 添加导航
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = spine
            
            # 保存文件
            epub.write_epub(filepath, book, {})
            self.log(f"增强EPUB文件保存成功: {filepath}")
            return True
            
        except Exception as e:
            self.log(f"保存增强EPUB文件失败: {str(e)}")
            return False
    
    def append_chapter_to_txt(self, filepath, chapter_title, chapter_content):
        """追加章节到TXT文件"""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f'{chapter_title}\n')
                f.write(chapter_content + '\n\n')
            return True
        except Exception as e:
            self.log(f"追加章节到TXT文件失败: {str(e)}")
            return False
    
    def create_directory(self, path):
        """创建目录"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.log(f"创建目录失败: {str(e)}")
            return False