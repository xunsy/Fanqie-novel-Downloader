# -*- coding: utf-8 -*-

import requests
import urllib.parse

class TomatoAPI:
    def __init__(self):
        self.base_url = "https://qwq.tutuxka.top/api/index.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _request(self, params):
        try:
            # 构建完整URL用于调试
            full_url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            print(f"Requesting URL: {full_url}")
            
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=100)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            json_data = response.json()
            print(f"Response JSON: {json_data}")  # 添加调试信息
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
            return None

    def get_content(self, item_ids=None, api_type=None, ts=None, book_id=None, comment=None, custom_url=None):
        params = {'api': 'content'}
        if item_ids:
            params['item_ids'] = item_ids
        if api_type:
            params['api_type'] = api_type
        if ts:
            params['ts'] = ts
        if book_id:
            params['book_id'] = book_id
        if comment:
            params['comment'] = comment
        if custom_url:
            params['custom_url'] = custom_url
        return self._request(params)

    def get_chapter(self, item_id):
        params = {'api': 'chapter', 'item_id': item_id}
        return self._request(params)

    def get_book_info(self, book_id):
        params = {'api': 'book', 'bookId': book_id}
        return self._request(params)

    def search(self, keyword, tab_type='novel'):
        # 确保搜索小说类型，不包括听书
        params = {'api': 'search', 'key': keyword, 'tab_type': tab_type}
        return self._request(params)

    def get_video(self, item_id):
        params = {'api': 'video', 'ts': '短剧', 'item_id': item_id}
        return self._request(params)

    def get_directory(self, fq_id):
        params = {'api': 'directory', 'fq_id': fq_id}
        return self._request(params)

    def get_item_info(self, item_ids):
        params = {'api': 'item_info', 'item_ids': item_ids}
        return self._request(params)

    def get_full_content(self, book_id, item_ids):
        params = {'api': 'full', 'book_id': book_id, 'item_ids': item_ids}
        return self._request(params)

    def get_ios_content(self, item_id):
        params = {'api': 'ios_content', 'item_id': item_id}
        return self._request(params)

    def get_manga(self, item_ids, show_html=None):
        params = {'api': 'manga', 'item_ids': item_ids}
        if show_html:
            params['show_html'] = show_html
        return self._request(params)