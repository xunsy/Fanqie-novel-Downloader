import unittest
import json
import time
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add src/python to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, save_json, load_json

class TestApi(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        # Mock file operations
        self.mock_config = {"savePath": "/tmp/novels", "concurrentDownloads": 3}
        self.mock_history = []
        
        # Use mock_open to patch file reading/writing
        self.m_open = mock_open()
        # When load_json is called, it will use our mock_open
        # We need to handle the case where the file doesn't exist initially
        def side_effect(path, *args, **kwargs):
            if "config.json" in path and 'r' in args:
                return mock_open(read_data=json.dumps(self.mock_config))()
            if "history.json" in path and 'r' in args:
                return mock_open(read_data=json.dumps(self.mock_history))()
            if 'w' in args:
                return self.m_open(path, *args, **kwargs)
            # Fallback for non-existent files on first read
            raise FileNotFoundError

        self.file_patcher = patch('builtins.open', side_effect=side_effect)
        self.file_patcher.start()
        
        # Reload modules to use patched open
        import main
        import importlib
        importlib.reload(main)
        self.app = main.app.test_client()
        
        # Reset global state
        main.downloader_instance = None
        main.download_thread = None
        main.config = self.mock_config.copy()
        main.history = self.mock_history.copy()

    def tearDown(self):
        self.file_patcher.stop()

    def test_get_settings(self):
        response = self.app.get('/api/settings')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['savePath'], '/tmp/novels')

    def test_update_settings(self):
        new_settings = {"savePath": "/new/path", "concurrentDownloads": 10}
        response = self.app.post('/api/settings', data=json.dumps(new_settings), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify settings were updated in the (mocked) file
        # The handle for the write call is the last one in the mock_calls list
        written_data = self.m_open.mock_calls[-1].args
        self.assertIn('"savePath": "/new/path"', written_data)
        self.assertIn('"concurrentDownloads": 10', written_data)

    def test_get_history_empty(self):
        response = self.app.get('/api/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_clear_history(self):
        # First, add something to history
        import main
        main.history.append({"novelId": "123", "title": "Test Book"})
        
        response = self.app.delete('/api/history')
        self.assertEqual(response.status_code, 200)
        
        # Verify history is now empty
        self.assertEqual(main.history, [])
        written_data = self.m_open.mock_calls[-1].args
        self.assertEqual(written_data, '[]')

    @patch('main.NovelDownloader')
    def test_full_download_flow_and_history(self, MockNovelDownloader):
        # --- 1. Start Download ---
        mock_downloader = MagicMock()
        # Simulate a successful download and return status
        mock_downloader.get_status.return_value = {"status": "completed", "title": "Great Novel"}
        # Make run_download do nothing
        mock_downloader.run_download.return_value = None
        MockNovelDownloader.return_value = mock_downloader
        
        response = self.app.post('/api/download', data=json.dumps({'book_id': '999'}), content_type='application/json')
        self.assertEqual(response.status_code, 202)

        # --- 2. Wait for thread to "finish" and check history ---
        import main
        # In a real scenario the thread would run, here we just join it
        main.download_thread.join() 
        
        self.assertEqual(len(main.history), 1)
        self.assertEqual(main.history['novelId'], '999')
        self.assertEqual(main.history['title'], 'Great Novel')

        # --- 3. Get history API should return the new entry ---
        response = self.app.get('/api/history')
        self.assertEqual(response.status_code, 200)
        history_data = json.loads(response.data)
        self.assertEqual(len(history_data), 1)
        self.assertEqual(history_data['novelId'], '999')

if __name__ == '__main__':
    unittest.main()