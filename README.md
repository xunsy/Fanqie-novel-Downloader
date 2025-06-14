# 当前项目部分源代码来源：https://github.com/Dlmily/Tomato-Novel-Downloader-Lite

# 番茄小说下载器 v1.7

一个功能强大的番茄小说下载工具，支持现代化GUI界面和命令行操作。

## ✨ 功能特点

### 🎯 核心功能
- 🖥️ **现代化GUI界面** - 美观整洁的界面设计，完美对齐的按钮布局
- 🌐 **智能API管理** - 自动从服务器获取最新API列表，确保下载稳定性
- ⚡ **批量下载模式** - 大量章节时自动启用批量下载，显著提升效率
- 📖 **多种输出格式** - 支持TXT、EPUB格式输出
- 📊 **实时进度显示** - 详细的下载状态、进度条和章节计数

### 🚀 增强功能
- 🔒 **Tor网络支持** - 内置Tor代理，保护隐私和绕过网络限制
- 🌍 **Cloudflare Workers反代** - 支持自定义反向代理，解决API访问问题
- ⚡ **多线程下载** - 智能并发控制，最大化下载速度
- 🔄 **断点续传** - 支持暂停和恢复下载，避免重复下载

### 🛠️ 技术特性
- 🎨 **响应式界面** - 网格布局系统，完美适配不同窗口大小
- 🔄 **智能重试机制** - 多API轮询，自动错误处理和重试
- 📝 **详细日志系统** - 完整的操作记录和错误信息
- 🔧 **模块化架构** - 清晰的代码结构，易于扩展和维护

## 📋 安装要求

- **Python 3.8+**
- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **内存**: 至少 512MB 可用内存
- **网络**: 稳定的互联网连接

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/POf-L/Fanqie-novel-Downloader.git
cd Fanqie-novel-Downloader

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动程序

#### GUI版本（推荐）
```bash
python main.py
```

#### 命令行版本
```bash
python cli.py
```

## 📖 使用指南

### 基本使用

1. **启动程序** - 运行 `python main.py` 启动GUI界面
2. **输入小说ID** - 在输入框中输入番茄小说的ID或书名
3. **选择保存路径** - 点击浏览按钮选择保存位置
4. **选择输出格式** - 选择TXT或EPUB格式
5. **开始下载** - 点击"开始下载"按钮，程序会自动获取API列表并开始下载

### 高级功能

#### 智能下载模式
- **自动API管理** - 程序启动时自动从服务器获取最新可用API列表
- **批量下载优化** - 超过100章节时自动启用批量下载模式，大幅提升速度
- **智能重试** - 多API轮询，单个API失败时自动切换到下一个

#### 配置Tor代理
1. 安装并启动Tor服务（推荐使用Tor Browser Bundle）
2. 在设置中启用Tor代理功能
3. 使用内置测试功能验证连接状态
4. 程序会自动通过Tor网络进行下载

#### Cloudflare Workers反代
1. 部署Cloudflare Workers反代脚本（参考docs目录）
2. 在设置中启用反代功能并填入Worker域名
3. 测试连接确保反代正常工作
4. 反代失败时程序会自动回退到原始URL

#### 调整下载参数
1. **并发设置** - 在设置中调整最大并发下载数（1-10）
2. **超时配置** - 根据网络情况调整请求超时时间
3. **速率限制** - 设置请求频率避免被服务器限制
4. **格式选项** - 启用TXT时自动生成EPUB功能

## 📁 项目结构

```
Fanqie-novel-Downloader/
├── assets/                     # 图标和资源文件
├── main.py                     # GUI版本入口
├── cli.py                      # 命令行版本
├── gui.py                      # GUI界面实现
├── config.py                   # 配置管理
├── downloader.py               # 新版下载核心
├── utils.py                    # 工具函数
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明
```

## ⚙️ 配置说明

程序会自动创建 `user_config.json` 配置文件，主要配置项：

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

## 🚀 新版本特性 v1.7

### 🌟 全新下载核心
- **智能API管理** - 自动从服务器获取最新API列表，无需手动更新
- **批量下载算法** - 大量章节时自动启用批量模式，下载速度提升10倍以上
- **多API轮询** - 支持多个API源，单个失败时自动切换
- **智能重试机制** - 网络异常时自动重试，确保下载完整性

### 🎨 界面全面美化
- **网格布局系统** - 所有按钮和元素完美对齐
- **响应式设计** - 适配不同窗口大小，布局始终整洁
- **视觉优化** - 统一的间距、字体和颜色搭配
- **用户体验提升** - 更直观的操作流程和状态显示

### ⚡ 性能大幅提升
- **批量下载** - 超过100章节时自动启用，速度提升显著
- **内存优化** - 降低内存占用，支持更大的小说下载
- **网络优化** - 智能请求频率控制，避免被服务器限制
- **错误处理** - 更完善的异常处理和恢复机制

## 🌐 Cloudflare Workers 反代支持

为了解决API访问被封锁的问题，本项目支持使用 Cloudflare Workers 作为反向代理。

### 快速部署

1. **部署 Worker**：使用提供的反代脚本部署到Cloudflare Workers
2. **配置反代**：在设置中启用反代功能并填入 Worker 域名
3. **测试连接**：使用内置测试功能验证配置

### 优势

- ✅ **免费使用**：Cloudflare 免费计划每天10万次请求
- ✅ **全球加速**：利用 Cloudflare 全球边缘网络
- ✅ **自动回退**：反代失败时自动使用原始URL
- ✅ **简单配置**：一键启用，无需复杂设置

## 🔧 故障排除

### 常见问题

1. **下载失败** - 检查网络连接和小说ID是否正确，确保API服务器可访问
2. **速度慢** - 调整并发数和请求间隔设置，启用批量下载模式
3. **被拦截** - 启用Tor代理、Cloudflare反代或降低请求频率
4. **反代失败** - 检查Worker部署状态和域名配置
5. **API获取失败** - 检查服务器连接，程序会自动重试获取API列表
6. **批量下载异常** - 检查网络稳定性，程序会自动回退到单章下载模式

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

### 开发指南
1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本工具仅用于技术学习和研究目的。使用者应当：

- 遵守相关法律法规和网站服务条款
- 尊重版权，不得用于商业用途
- 合理控制下载频率，避免对服务器造成压力
- 承担使用本工具的所有风险和责任

作者不承担因使用本工具而产生的任何法律责任。

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**

---

## 配置文件

为了更好地遵循不同操作系统的规范并提高应用的健壮性，用户配置文件 (`user_config.json`) 现在存储在系统推荐的标准位置。

-   **Windows**: `C:\Users\<你的用户名>\AppData\Local\User\TomatoNovelDownloader\user_config.json`
-   **macOS**: `~/Library/Application Support/TomatoNovelDownloader/user_config.json`
-   **Linux**: `~/.config/TomatoNovelDownloader/user_config.json`

这一改动使得应用不再将配置文件散落在程序目录中，更加整洁和规范。
