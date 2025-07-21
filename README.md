# 🍅 番茄小说下载器

一个功能强大的番茄小说下载工具，支持批量下载、章节完整性验证、自动更新等功能。

<div align="center">

### 📈 项目状态</div>

[![GitHub release](https://img.shields.io/github/v/release/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=github&color=blue)](https://github.com/POf-L/Fanqie-novel-Downloader/releases)
[![GitHub downloads](https://img.shields.io/github/downloads/POf-L/Fanqie-novel-Downloader/total?style=for-the-badge&logo=download&color=green)](https://github.com/POf-L/Fanqie-novel-Downloader/releases)
[![GitHub stars](https://img.shields.io/github/stars/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=star&color=yellow)](https://github.com/POf-L/Fanqie-novel-Downloader/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=fork&color=orange)](https://github.com/POf-L/Fanqie-novel-Downloader/network)
[![GitHub issues](https://img.shields.io/github/issues/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=github&color=red)](https://github.com/POf-L/Fanqie-novel-Downloader/issues)
[![GitHub license](https://img.shields.io/github/license/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=opensourceinitiative&color=purple)](https://github.com/POf-L/Fanqie-novel-Downloader/blob/main/LICENSE)

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)](https://www.microsoft.com/windows/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/POf-L/Fanqie-novel-Downloader/build-release.yml?style=for-the-badge&logo=github-actions)](https://github.com/POf-L/Fanqie-novel-Downloader/actions)
[![Last Commit](https://img.shields.io/github/last-commit/POf-L/Fanqie-novel-Downloader?style=for-the-badge&logo=git)](https://github.com/POf-L/Fanqie-novel-Downloader/commits)

[![Repo Size](https://img.shields.io/github/repo-size/POf-L/Fanqie-novel-Downloader?style=flat-square&logo=github)](https://github.com/POf-L/Fanqie-novel-Downloader)
[![Code Size](https://img.shields.io/github/languages/code-size/POf-L/Fanqie-novel-Downloader?style=flat-square&logo=python)](https://github.com/POf-L/Fanqie-novel-Downloader)
[![Top Language](https://img.shields.io/github/languages/top/POf-L/Fanqie-novel-Downloader?style=flat-square&logo=python)](https://github.com/POf-L/Fanqie-novel-Downloader)
[![Language Count](https://img.shields.io/github/languages/count/POf-L/Fanqie-novel-Downloader?style=flat-square)](https://github.com/POf-L/Fanqie-novel-Downloader)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=POf-L.Fanqie-novel-Downloader)](https://github.com/POf-L/Fanqie-novel-Downloader)

</div>

## ✨ 主要特性

- 🔍 **智能搜索**：支持关键词搜索，快速找到目标小说
- 📚 **批量下载**：高效的批量下载机制，支持大型小说
- 🔧 **章节验证**：自动验证章节完整性，补充缺失章节
- 📖 **格式优化**：自动修复章节顺序，生成规范的文本文件
- 🚀 **自动更新**：基于GitHub Actions的自动更新系统
- 🎨 **现代界面**：美观的图形用户界面，操作简单直观
- ⚡ **高性能**：优化的下载算法，遵循API限制确保稳定性

## 🚀 快速开始

### 方法一：下载可执行文件（推荐）

1. 前往 [Releases](https://github.com/POf-L/Fanqie-novel-Downloader/releases) 页面
2. 下载最新版本的 `TomatoNovelDownloader-*.zip`
3. 解压并运行 `TomatoNovelDownloader-*.exe`

### 方法二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/POf-L/Fanqie-novel-Downloader.git
cd Fanqie-novel-Downloader

# 安装依赖
pip install -r requirements.txt

# 运行程序
python GUI.py
```

## 📖 使用说明

### 基本操作

1. **搜索小说**
   - 在搜索框输入关键词
   - 点击"搜索"按钮或按回车键
   - 从结果列表中选择目标小说

2. **下载小说**
   - 双击搜索结果中的小说，或手动输入书籍ID
   - 点击"开始下载"按钮
   - 等待下载完成

3. **查看结果**
   - 下载的小说保存为 `.txt` 文件
   - 文件名为书籍名称（已清理特殊字符）
   - 章节按正确顺序排列

### 高级功能

- **章节验证**：程序会自动检查下载的章节完整性
- **自动补充**：发现缺失章节时会自动重新下载
- **备份机制**：修复章节顺序前会自动创建备份文件
- **批量处理**：支持使用 `fix_chapter_order.py` 批量修复已下载的文件

## 🛠️ 技术特性

### 核心功能

- **API优化**：遵循30章/批次的API限制，确保下载稳定性
- **错误处理**：完善的异常处理和重试机制
- **内存优化**：流式下载，支持大型小说文件
- **编码支持**：完整的UTF-8编码支持

### 章节验证算法

```python
# 智能章节匹配
def match_chapters(original, downloaded):
    - 标题完全匹配
    - 标题包含匹配  
    - 章节号匹配（支持多种格式）
    - 模糊相似度匹配
```

### 自动更新系统

- 基于GitHub Actions自动构建
- 时间戳版本号：`YYYY.MM.DD.HHMM-commit`
- 增量更新和完整性验证
- 用户友好的更新界面

## 📁 项目结构

```
Fanqie-novel-Downloader/
├── GUI.py                    # 主程序界面
├── api.py                    # API接口封装
├── updater.py               # 自动更新模块
├── fix_chapter_order.py     # 章节排序工具
├── version.py               # 版本信息
├── requirements.txt         # 依赖列表
├── .github/workflows/       # GitHub Actions配置
│   └── build-release.yml    # 自动构建和发布
├── build.spec              # PyInstaller配置
└── README.md               # 项目说明
```

## 🔧 开发环境

### 环境要求

- Python 3.8+
- Windows 10/11（推荐）
- 网络连接

### 依赖包

```txt
requests>=2.28.0
tkinter (Python内置)
pathlib (Python内置)
threading (Python内置)
```

### 构建可执行文件

```bash
# 安装PyInstaller
pip install pyinstaller

# 使用配置文件构建
pyinstaller build.spec

# 或者直接构建
pyinstaller --onefile --windowed --name "TomatoNovelDownloader" GUI.py
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

### 代码规范

- 使用中文注释
- 遵循PEP 8代码风格
- 添加适当的错误处理
- 编写清晰的提交信息

## 📝 更新日志

### v2025.01.21.1200 (最新)

- ✅ 修复API批次限制问题（100章→30章）
- ✅ 优化章节完整性验证算法
- ✅ 改进批量补充缺失章节功能
- ✅ 增强错误处理和日志记录
- ✅ 添加自动更新系统

### 历史版本

查看完整更新日志：[Releases](https://github.com/POf-L/Fanqie-novel-Downloader/releases)

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关法律法规和网站服务条款。

- 请勿用于商业用途
- 请勿过度频繁请求API
- 下载的内容请勿二次传播
- 使用本工具产生的任何后果由用户自行承担

## 📊 项目统计

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=POf-L/Fanqie-novel-Downloader&type=Date)](https://star-history.com/#POf-L/Fanqie-novel-Downloader&Date)

### 贡献者统计

[![Contributors](https://contrib.rocks/image?repo=POf-L/Fanqie-novel-Downloader)](https://github.com/POf-L/Fanqie-novel-Downloader/graphs/contributors)

### GitHub统计卡片

<div align="center">

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=POf-L&repo=Fanqie-novel-Downloader&show_icons=true&theme=radical)

![Top Languages](https://github-readme-stats.vercel.app/api/top-langs/?username=POf-L&layout=compact&theme=radical)

</div>

### 提交活动

![GitHub Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=POf-L&repo=Fanqie-novel-Downloader&theme=react-dark)

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🙏 致谢

- 感谢 [@rabbits0209](https://github.com/rabbits0209) 贡献提供的API接口
- 感谢所有贡献者和用户的支持
- 感谢开源社区的技术支持
- 感谢 [Star History](https://star-history.com/) 提供的统计图表
- 感谢 [Shields.io](https://shields.io/) 提供的徽章服务

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

[![GitHub stars](https://img.shields.io/github/stars/POf-L/Fanqie-novel-Downloader?style=social)](https://github.com/POf-L/Fanqie-novel-Downloader/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/POf-L/Fanqie-novel-Downloader?style=social)](https://github.com/POf-L/Fanqie-novel-Downloader/network)
[![GitHub watchers](https://img.shields.io/github/watchers/POf-L/Fanqie-novel-Downloader?style=social)](https://github.com/POf-L/Fanqie-novel-Downloader/watchers)

[🐛 报告Bug](https://github.com/POf-L/Fanqie-novel-Downloader/issues) |
[💡 功能建议](https://github.com/POf-L/Fanqie-novel-Downloader/issues) |
[💬 讨论区](https://github.com/POf-L/Fanqie-novel-Downloader/discussions)

</div>
