# 番茄小说下载器 v1.7

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/status-active-brightgreen.svg" alt="Status">
</p>

<p align="center">
  一个功能强大的番茄小说下载工具，支持现代化GUI界面和命令行操作。
</p>

---

## 🖼️ 应用截图

*在这里添加应用的截图，展示其美观的界面。*

![App Screenshot Placeholder](https://via.placeholder.com/800x500.png?text=App+Screenshot+Here)

---

## ✨ 功能特点

### 🎯 核心功能
- 🖥️ **现代化GUI界面**: 美观整洁的界面设计，完美对齐的按钮布局。
- 🌐 **智能API管理**: 自动从服务器获取最新API列表，确保下载稳定性。
- ⚡ **批量下载模式**: 大量章节时自动启用批量下载，显著提升效率。
- 📖 **多种输出格式**: 支持 `TXT` 和 `EPUB` 格式输出。
- 📊 **实时进度显示**: 详细的下载状态、进度条和章节计数。

### 🚀 增强功能
- 🔒 **Tor网络支持**: 内置Tor代理，保护隐私和绕过网络限制。
- 🌍 **Cloudflare Workers反代**: 支持自定义反向代理，解决API访问问题。
- ⚡ **多线程下载**: 智能并发控制，最大化下载速度。
- 🔄 **断点续传**: 支持暂停和恢复下载，避免重复下载。

### 🛠️ 技术特性
- 🎨 **响应式界面**: 网格布局系统，完美适配不同窗口大小。
- 🔄 **智能重试机制**: 多API轮询，自动错误处理和重试。
- 📝 **详细日志系统**: 完整的操作记录和错误信息。
- 🔧 **模块化架构**: 清晰的代码结构，易于扩展和维护。

---

## 🚀 快速开始

### 📋 安装要求
- **Python**: 3.8+
- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **内存**: 至少 512MB 可用内存
- **网络**: 稳定的互联网连接

### ⚙️ 安装步骤

1.  **克隆项目**
    ```bash
    git clone https://github.com/POf-L/Fanqie-novel-Downloader.git
    cd Fanqie-novel-Downloader
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

    > **注意**: 如果遇到 `tkinter` 安装错误，请参考 [TKINTER_SETUP.md](TKINTER_SETUP.md) 获取详细解决方案。

### ▶️ 启动程序

-   **GUI版本 (推荐)**:
    ```bash
    python main.py
    ```
-   **命令行版本**:
    ```bash
    python cli.py
    ```

---

## 📖 使用指南

1.  **启动程序**: 运行 `python main.py` 启动GUI界面。
2.  **输入小说ID**: 在输入框中输入番茄小说的ID或书名。
3.  **选择保存路径**: 点击浏览按钮选择保存位置。
4.  **选择输出格式**: 选择 `TXT` 或 `EPUB` 格式。
5.  **开始下载**: 点击"开始下载"按钮，程序会自动获取API列表并开始下载。

---

## ⚙️ 配置

程序会自动在标准用户数据目录中创建 `user_config.json` 配置文件。

### 配置文件位置
- **Windows**: `C:\Users\<YourUser>\AppData\Local\User\TomatoNovelDownloader\user_config.json`
- **macOS**: `~/Library/Application Support/TomatoNovelDownloader/user_config.json`
- **Linux**: `~/.config/TomatoNovelDownloader/user_config.json`

### 默认配置示例
```json
{
    "request": {
        "max_workers": 4,
        "timeout": 15,
        "request_rate_limit": 0.4
    },
    "file": {
        "default_save_path": "downloads"
    },
    "tor": {
        "enabled": false,
        "proxy_port": 9050,
        "change_ip_after": 980
    },
    "cloudflare_proxy": {
        "enabled": false,
        "proxy_domain": "",
        "fallback_to_original": true
    },
    "batch_download": {
        "enabled": true,
        "max_batch_size": 290,
        "auto_enable_threshold": 100
    }
}
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

1.  Fork 本项目。
2.  创建您的功能分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  将分支推送到远程 (`git push origin feature/AmazingFeature`)。
5.  创建一个 Pull Request。

---

## 📄 许可证

本项目采用 **MIT** 许可证。详见 `LICENSE` 文件。

---

## ⚠️ 免责声明

本工具仅用于技术学习和研究目的。使用者应承担使用本工具的所有风险和责任，作者不承担任何法律责任。

---

<p align="center">
  <strong>⭐ 如果这个项目对您有帮助，请给个Star支持一下！ ⭐</strong>
</p>

---
*部分源代码参考自：[Dlmily/Tomato-Novel-Downloader-Lite](https://github.com/Dlmily/Tomato-Novel-Downloader-Lite)*
