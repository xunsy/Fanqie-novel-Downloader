# 番茄小说下载器 v1.2.1

一个功能完整的番茄小说下载工具，支持GUI界面和命令行操作。

## ✨ 功能特点

### 🎯 核心功能
- 🖥️ **现代化GUI界面** - 操作简单直观，支持深色/浅色主题
- 📚 **API下载模式** - 使用官方API接口，稳定可靠
- 🔄 **断点续传** - 支持暂停和恢复下载
- 📖 **多种输出格式** - TXT、EPUB
- 📊 **实时进度显示** - 详细的下载状态和进度条

### 🚀 增强功能
- 📱 **图书馆管理** - 管理已下载的小说和收藏
- 🔒 **Tor代理支持** - 保护隐私和绕过限制
- ⚡ **多线程下载** - 提高下载速度和效率

### 🛠️ 技术特性
- 🎨 **可配置界面** - 丰富的设置选项和个性化配置
- 🔄 **自动重试机制** - 智能错误处理和重试
- 📝 **详细日志** - 完整的操作记录和错误信息
- 🔧 **模块化设计** - 易于扩展和维护

## 📋 安装要求

- **Python 3.8+**
- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **内存**: 至少 512MB 可用内存
- **网络**: 稳定的互联网连接

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/Tomato-Novel-Downloader.git
cd Tomato-Novel-Downloader

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

1. **启动程序** - 运行 `python main.py`
2. **输入小说ID** - 在输入框中输入番茄小说的ID
3. **选择保存路径** - 点击浏览按钮选择保存位置
4. **选择输出格式** - 选择TXT或EPUB格式
5. **开始下载** - 点击"开始下载"按钮

### 高级功能

#### 配置Tor代理
1. 安装并启动Tor服务
2. 在设置中启用Tor代理
3. 测试连接确保正常工作

#### 调整下载参数
1. 在设置中调整并发数和超时时间
2. 根据网络情况优化请求频率
3. 启用EPUB自动生成功能

## 📁 项目结构

```
Tomato-Novel-Downloader/
├── assets/                     # 图标资源
├── docs/                       # 文档目录
│   └── project_structure.md   # 项目结构
├── main.py                     # GUI版本入口
├── cli.py                      # 命令行版本
├── gui.py                      # GUI界面实现
├── config.py                   # 配置管理
├── downloader.py               # 下载器模块
├── utils.py                    # 工具函数
└── requirements.txt            # 依赖列表
```

## ⚙️ 配置说明

程序会自动创建 `user_config.json` 配置文件，主要配置项：

```json
{
    "request": {
        "max_workers": 5,
        "timeout": 10,
        "request_rate_limit": 0.2
    },
    "file": {
        "default_save_path": "downloads"
    },
    "tor": {
        "enabled": false,
        "proxy_port": 9050
    },
    "cloudflare_proxy": {
        "enabled": false,
        "proxy_domain": "",
        "fallback_to_original": true
    }
}
```

## 🌐 Cloudflare Workers 反代支持

为了解决API访问被封锁的问题，本项目支持使用 Cloudflare Workers 作为反向代理。

### 快速部署

1. **部署 Worker**：参考 [Cloudflare Workers 部署指南](docs/cloudflare-workers-guide.md)
2. **配置反代**：在设置中启用反代功能并填入 Worker 域名
3. **测试连接**：使用内置测试功能验证配置

### 优势

- ✅ **免费使用**：Cloudflare 免费计划每天10万次请求
- ✅ **全球加速**：利用 Cloudflare 全球边缘网络
- ✅ **自动回退**：反代失败时自动使用原始URL
- ✅ **简单配置**：一键启用，无需复杂设置

## 🔧 故障排除

### 常见问题

1. **下载失败** - 检查网络连接和小说ID是否正确
2. **速度慢** - 调整并发数和请求间隔设置
3. **被拦截** - 启用Tor代理、Cloudflare反代或降低请求频率
4. **反代失败** - 检查Worker部署状态和域名配置

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
