import unittest
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

# 将 src/python 添加到 python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from downloader.core import NovelDownloader

class TestNovelDownloader(unittest.TestCase):

    def setUp(self):
        self.book_id = "test_book_id"
        self.save_path = "./test_novels"
        os.makedirs(self.save_path, exist_ok=True)
        self.downloader = NovelDownloader(self.book_id, self.save_path)

    def tearDown(self):
        if os.path.exists(self.save_path):
            shutil.rmtree(self.save_path)

    @patch('downloader.core.NovelDownloader._make_request')
    def test_get_book_info_success(self, mock_request):
        # 模拟一个成功的 HTML 响应
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <h1>测试书籍</h1>
            <div class='author-name-text'>测试作者</div>
            <div class='page-abstract-content'><p>这是一个测试简介。</p></div>
        </html>
        """
        mock_request.return_value = mock_response

        result = self.downloader.get_book_info()
        self.assertTrue(result)
        self.assertEqual(self.downloader.book_info['name'], '测试书籍')
        self.assertEqual(self.downloader.book_info['author'], '测试作者')
        self.assertEqual(self.downloader.book_info['description'], '这是一个测试简介。')

    @patch('downloader.core.NovelDownloader._make_request')
    def test_get_chapter_list_success(self, mock_request):
        # 模拟 API 和网页的成功响应
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {
            "data": {"allItemIds": ["chap1", "chap2"]}
        }
        
        mock_page_response = MagicMock()
        mock_page_response.text = """
        <html>
            <div class="chapter-item"><a href="/page/chap1">第一章 标题一</a></div>
            <div class="chapter-item"><a href="/page/chap2">第二章 标题二</a></div>
        </html>
        """
        mock_request.side_effect = [mock_api_response, mock_page_response]

        result = self.downloader.get_chapter_list()
        self.assertTrue(result)
        self.assertEqual(len(self.downloader.chapters), 2)
        self.assertEqual(self.downloader.chapters['id'], 'chap1')
        self.assertIn('标题一', self.downloader.chapters['title'])

    def test_process_chapter_content(self):
        raw_content = "<header>ignore</header><p>  paragraph 1 </p><p>paragraph 2</p><footer>ignore</footer>"
        processed = self.downloader._process_chapter_content(raw_content)
        self.assertIn("paragraph 1", processed)
        self.assertIn("paragraph 2", processed)
        self.assertNotIn("ignore", processed)
        self.assertTrue(processed.startswith("    "))

    @patch('downloader.core.NovelDownloader._download_single_chapter')
    @patch('downloader.core.NovelDownloader.get_book_info', return_value=True)
    @patch('downloader.core.NovelDownloader.get_chapter_list', return_value=True)
    def test_run_download_txt(self, mock_get_list, mock_get_info, mock_download_chapter):
        # 设置模拟数据
        self.downloader.chapters = [{"id": "chap1", "title": "第一章", "index": 0}]
        self.downloader.book_info = {"name": "测试书籍", "author": "作者", "description": "简介"}
        
        mock_download_chapter.return_value = {
            "title": "API标题",
            "content": "这是章节内容。"
        }

        self.downloader.run_download()

        # 验证文件是否创建
        expected_file = os.path.join(self.save_path, "测试书籍.txt")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("小说名: 测试书籍", content)
            self.assertIn("第一章", content)
            self.assertIn("这是章节内容。", content)

if __name__ == '__main__':
    unittest.main()