import time
import requests
import bs4
import re
import os
import random
import json
import urllib3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from typing import Optional, Dict, List, Any
from ebooklib import epub

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NovelDownloader:
    """
    小说下载器核心类
    """
    def __init__(self, book_id, save_path, file_format='txt'):
        self.book_id = book_id
        self.save_path = save_path
        self.file_format = file_format
        self.headers = self._get_headers()
        self.session = requests.Session()

        self.config = {
            "max_workers": 16,
            "max_retries": 3,
            "request_timeout": 15,
            "status_file": "chapter.json",
            "request_rate_limit": 0.4,
        }

        self.book_info = {}
        self.chapters: List[Dict[str, Any]] = [] # 将包含章节信息和状态
        self.chapter_results = {}
        self.status = "idle"  # idle, downloading, completed, error
        self.error_message: Optional[str] = None
        self.output_filepath = None
        self._chapter_map_by_id: Dict[str, Dict[str, Any]] = {}

    def _get_headers(self) -> Dict[str, str]:
        """生成随机请求头"""
        ua = UserAgent()
        return {
            "User-Agent": ua.random,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://fanqienovel.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }

    def _make_request(self, url, method='GET', **kwargs):
        """通用的请求函数"""
        kwargs.setdefault('timeout', self.config["request_timeout"])
        kwargs.setdefault('verify', False)
        kwargs.setdefault('headers', self.headers)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"请求超时: {url}")
            raise  # 重新引发异常，让调用者处理
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"资源未找到: {url}")
            else:
                print(f"HTTP错误: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            raise

    def get_book_info(self):
        """获取书名、作者、简介"""
        url = f'https://fanqienovel.com/page/{self.book_id}'
        try:
            response = self._make_request(url)
            if not response:
                self.error_message = "获取书籍信息时网络请求失败"
                return False

            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            
            name_tag = soup.find('h1')
            if not name_tag or not name_tag.text.strip():
                self.error_message = "无效的小说ID或页面结构已更改"
                return False

            name = name_tag.text
            
            author_name = "未知作者"
            author_element = soup.find('div', class_='author-name-text')
            if author_element:
                author_name = author_element.text

            description = "无简介"
            desc_element = soup.find('div', class_='page-abstract-content')
            if desc_element and desc_element.find('p'):
                description = desc_element.find('p').text

            self.book_info = {
                "name": name,
                "author": author_name,
                "description": description
            }
            return True
        except requests.exceptions.Timeout:
            self.error_message = "获取书籍信息超时"
            return False
        except requests.exceptions.RequestException:
            self.error_message = "获取书籍信息时网络连接失败"
            return False
        except Exception as e:
            self.error_message = f"解析书籍信息时发生未知错误: {e}"
            print(f"获取书籍信息失败: {str(e)}")
            return False

    def get_chapter_list(self):
        """获取章节列表"""
        try:
            api_url = f"https://fanqienovel.com/api/reader/directory/detail?bookId={self.book_id}"
            response = self._make_request(api_url)
            if not response:
                self.error_message = "获取章节列表时网络请求失败"
                return False
            
            api_data = response.json()
            if api_data.get("code") != 0 or "data" not in api_data:
                self.error_message = "获取章节列表API返回错误"
                return False

            chapter_ids = api_data.get("data", {}).get("allItemIds", [])
            if not chapter_ids:
                self.error_message = "未能从此书籍ID获取到任何章节"
                return False

            # 为了获取标题，我们仍然需要访问网页
            page_url = f'https://fanqienovel.com/page/{self.book_id}'
            page_response = self._make_request(page_url)
            if not page_response:
                 print("无法获取网页版章节列表，将使用默认标题")
                 web_chapters = {}
            else:
                soup = bs4.BeautifulSoup(page_response.text, 'html.parser')
                web_chapters_list = soup.select('div.chapter-item a')
                web_chapters = {
                    item['href'].split('/')[-1]: item.get_text(strip=True)
                    for item in web_chapters_list if item.has_attr('href')
                }

            final_chapters = []
            for idx, chapter_id in enumerate(chapter_ids):
                raw_title = web_chapters.get(chapter_id, f"第{idx+1}章")
                
                if re.match(r'^(番外|特别篇|if线)\s*', raw_title):
                    final_title = raw_title
                else:
                    clean_title = re.sub(r'^第[一二三四五六七八九十百千\d]+章\s*', '', raw_title).strip()
                    final_title = f"第{idx+1}章 {clean_title}"

                final_chapters.append({
                    "id": chapter_id,
                    "title": final_title,
                    "index": idx,
                    "status": "pending" # pending, downloading, completed, failed
                })

            self.chapters = final_chapters
            # 创建一个 ID 到章节的映射，方便快速更新状态
            self._chapter_map_by_id = {ch['id']: ch for ch in self.chapters}
            return True
        except requests.exceptions.Timeout:
            self.error_message = "获取章节列表超时"
            return False
        except requests.exceptions.RequestException:
            self.error_message = "获取章节列表时网络连接失败"
            return False
        except Exception as e:
            self.error_message = f"解析章节列表时发生未知错误: {e}"
            print(f"获取章节列表失败: {str(e)}")
            return False

    def _process_chapter_content(self, content: str) -> str:
        """处理章节内容"""
        if not content:
            return ""
        try:
            # 基础清理
            content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
            content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
            content = re.sub(r'</?article>', '', content)
            
            # 提取段落
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
            if not paragraphs:
                # 如果没有 p 标签，直接清理所有 HTML 标签
                cleaned_content = re.sub(r'<[^>]+>', '', content)
            else:
                cleaned_content = "\n".join(p.strip() for p in paragraphs if p.strip())

            # 格式化
            formatted_content = '\n'.join('    ' + line if line.strip() else '' for line in cleaned_content.split('\n'))
            formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content).strip()
            
            return formatted_content
        except Exception as e:
            print(f"内容处理错误: {e}")
            return content # 返回原始内容以供调试

    def _download_single_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """下载单个章节内容"""
        # 这里简化为只使用 fanqie_sdk API
        url = "https://fanqienovel.com/api/reader/full"
        params = {
            "sdk_type": "4",
            "novelsdk_aid": "638505",
            "item_id": chapter_id,
            "need_book_info": "1",
        }
        
        try:
            response = self._make_request(url, params=params)
            if not response:
                return None

            data = response.json().get("data", {})
            content = data.get("content", "")
            processed_content = self._process_chapter_content(content)
            
            return {
                "title": data.get("title", ""),
                "content": processed_content
            }
        except Exception as e:
            print(f"下载章节 {chapter_id} 失败: {e}")
            return None

    def run_download(self):
        """执行下载任务"""
        self.status = "downloading"
        self.error_message = None # 重置错误信息
        
        if not self.get_book_info() or not self.get_chapter_list():
            self.status = "error"
            # error_message 已经在 get_book_info 或 get_chapter_list 中设置
            print(f"初始化失败: {self.error_message}")
            return

        os.makedirs(self.save_path, exist_ok=True)
        
        # 筛选出所有未完成的章节
        todo_chapters = [ch for ch in self.chapters if ch["status"] != "completed"]
        
        # 将待下载章节状态更新为 "downloading"
        for ch in todo_chapters:
            ch['status'] = 'downloading'
            
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            future_to_chapter = {executor.submit(self._download_single_chapter, ch['id']): ch for ch in todo_chapters}
            
            for future in as_completed(future_to_chapter):
                chapter_data = future_to_chapter[future]
                chapter_id = chapter_data['id']
                chapter_obj = self._chapter_map_by_id.get(chapter_id)

                try:
                    result = future.result()
                    if result and result['content']:
                        self.chapter_results[chapter_data['index']] = {
                            "base_title": chapter_data['title'],
                            "api_title": result['title'],
                            "content": result['content']
                        }
                        if chapter_obj: chapter_obj['status'] = 'completed'
                    else:
                        if chapter_obj: chapter_obj['status'] = 'failed'
                except Exception as exc:
                    print(f'章节 {chapter_id} 生成异常: {exc}')
                    if chapter_obj: chapter_obj['status'] = 'failed'

        self._save_to_file()
        self.status = "completed"
        print("下载完成!")

    def _save_to_file(self):
        """根据格式保存文件"""
        output_filename = os.path.join(self.save_path, f"{self.book_info['name']}.{self.file_format}")
        self.output_filepath = output_filename

        if self.file_format == 'txt':
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(f"小说名: {self.book_info['name']}\n")
                f.write(f"作者: {self.book_info['author']}\n")
                f.write(f"简介: {self.book_info['description']}\n\n")
                
                sorted_chapters = sorted(self.chapter_results.items())
                for _, result in sorted_chapters:
                    title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                    f.write(f"{title}\n{result['content']}\n\n")
        
        elif self.file_format == 'epub':
            book = epub.EpubBook()
            book.set_identifier(f"book_{self.book_id}")
            book.set_title(self.book_info['name'])
            book.set_language('zh-CN')
            book.add_author(self.book_info['author'])
            book.add_metadata('DC', 'description', self.book_info['description'])
            
            toc = []
            spine = ['nav']
            
            sorted_chapters = sorted(self.chapter_results.items())
            for idx, result in sorted_chapters:
                title = f'{result["base_title"]} {result["api_title"]}' if result["api_title"] else result["base_title"]
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chap_{idx}.xhtml',
                    lang='zh-CN'
                )
                content = result['content'].replace('\n', '<br/>')
                chapter.content = f'<h1>{title}</h1><p>{content}</p>'.encode('utf-8')
                book.add_item(chapter)
                toc.append(chapter)
                spine.append(chapter)

            book.toc = tuple(toc)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = spine
            
            epub.write_epub(output_filename, book, {})

    def get_status(self):
        """获取当前下载状态和详细章节列表"""
        total = len(self.chapters)
        # 计算已完成的章节数
        downloaded = sum(1 for ch in self.chapters if ch['status'] == 'completed')
        progress = (downloaded / total * 100) if total > 0 else 0
        
        # 创建要返回的章节列表副本，避免直接暴露内部状态
        chapters_status_list = [
            {"title": ch["title"], "status": ch["status"]}
            for ch in self.chapters
        ]

        result = {
            "status": self.status,
            "total_chapters": total,
            "downloaded_chapters": downloaded,
            "progress": f"{progress:.2f}",
            "chapters": chapters_status_list,
            "book_info": self.book_info,
            "error_message": self.error_message
        }

        if self.status == 'completed':
            result['filePath'] = self.output_filepath
        
        return result

if __name__ == '__main__':
    # 测试代码
    test_book_id = "7090519035717225503" # 示例小说ID
    save_directory = "./novels"
    
    downloader = NovelDownloader(test_book_id, save_directory, file_format='txt')
    
    # 使用线程运行下载，避免阻塞
    download_thread = threading.Thread(target=downloader.run_download)
    download_thread.start()
    
    # 轮询状态
    while download_thread.is_alive():
        status = downloader.get_status()
        print(f"当前状态: {status['status']}, 进度: {status['progress']} ({status['downloaded_chapters']}/{status['total_chapters']})")
        time.sleep(2)
    
    # 打印最终状态
    print("最终状态:", downloader.get_status())