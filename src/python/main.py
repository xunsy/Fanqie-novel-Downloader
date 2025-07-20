from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import json
from downloader.core import NovelDownloader
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- 全局变量和配置 ---
downloader_instance = None
download_thread = None
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
HISTORY_FILE = os.path.join(os.getcwd(), "history.json")

# --- 辅助函数 ---
def load_json(file_path, default_data):
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default_data

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 初始化配置和历史 ---
config = load_json(CONFIG_FILE, {"savePath": os.path.join(os.getcwd(), "novels"), "concurrentDownloads": 3})
history = load_json(HISTORY_FILE, [])
os.makedirs(config['savePath'], exist_ok=True)

# --- API 端点 ---
@app.route('/api/download', methods=['POST'])
def start_download():
    global downloader_instance, download_thread
    data = request.get_json()
    if not data or 'book_id' not in data:
        return jsonify({"error": "缺少 'book_id' 参数"}), 400

    if download_thread and download_thread.is_alive():
        return jsonify({"error": "当前已有下载任务在进行中"}), 409

    book_id = data['book_id']
    downloader_instance = NovelDownloader(
        book_id=book_id,
        save_path=config['savePath'],
        file_format=data.get('file_type', 'txt')
    )

    def download_task_wrapper():
        downloader_instance.run_download()
        # 下载完成后记录历史
        status = downloader_instance.get_status()
        if status.get('status') == 'completed':
            add_to_history({
                "novelId": book_id,
                "title": status.get('title', '未知书籍'),
                "downloadedAt": datetime.now().isoformat()
            })

    download_thread = threading.Thread(target=download_task_wrapper)
    download_thread.start()
    return jsonify({"message": "下载任务已启动", "book_id": book_id}), 202

@app.route('/api/status', methods=['GET'])
def get_status():
    if not downloader_instance or not download_thread.is_alive():
        return jsonify({"status": "idle", "message": "当前没有下载任务"})
    return jsonify(downloader_instance.get_status())

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    global config
    if request.method == 'POST':
        new_settings = request.get_json()
        config.update(new_settings)
        save_json(CONFIG_FILE, config)
        os.makedirs(config['savePath'], exist_ok=True) # 确保新目录存在
        return jsonify({"success": True, "message": "设置已保存"})
    else: # GET
        return jsonify(config)

@app.route('/api/history', methods=['GET', 'DELETE'])
def handle_history():
    global history
    if request.method == 'DELETE':
        history.clear()
        save_json(HISTORY_FILE, history)
        return jsonify({"success": True, "message": "历史记录已清除"})
    else: # GET
        return jsonify(sorted(history, key=lambda x: x['downloadedAt'], reverse=True))

def add_to_history(entry):
    global history
    # 避免重复添加
    if not any(h['novelId'] == entry['novelId'] for h in history):
        history.insert(0, entry)
        save_json(HISTORY_FILE, history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)