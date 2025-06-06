# GitHub Actions 自动发布说明

## 🚀 功能介绍

本项目已配置GitHub Actions自动编译和发布功能，每次推送到main分支时会自动：

1. **编译exe文件** - 使用PyInstaller将Python项目编译为Windows可执行文件
2. **生成版本号** - 基于推送时间自动生成版本号（格式：v2025.06.07.1234）
3. **收集更新内容** - 自动获取最近20次git提交记录作为更新日志
4. **创建Release** - 在GitHub上创建新的发布版本
5. **上传文件** - 将编译好的exe文件上传到Release中

## 📁 相关文件

- `.github/workflows/auto-release.yml` - GitHub Actions工作流配置
- `build_exe.spec` - PyInstaller编译配置文件
- `requirements.txt` - Python依赖包列表

## 🔧 工作流程

### 触发条件
- 推送到 `main` 或 `master` 分支
- 手动触发（在GitHub Actions页面）

### 执行步骤
1. **环境准备**
   - 使用Windows最新版本的运行器
   - 安装Python 3.11
   - 安装项目依赖包

2. **编译过程**
   - 使用PyInstaller根据spec文件编译
   - 生成单个exe文件（约25MB）

3. **版本信息生成**
   - 版本号：`v年.月.日.时分`（如：v2025.06.07.1544）
   - 更新内容：最近20次提交的简要说明

4. **发布流程**
   - 创建GitHub Release
   - 上传编译好的exe文件
   - 添加详细的发布说明

## 📦 发布内容

每次自动发布包含：

### 文件
- `番茄小说下载器.exe` - 主程序可执行文件

### 发布说明
- 🚀 版本信息和发布时间
- 📝 最近20次提交的更新内容
- 💾 下载和使用说明
- ⚠️ 注意事项和常见问题

## 🛠️ 自定义配置

### 修改版本号格式
编辑 `.github/workflows/auto-release.yml` 文件中的版本号生成部分：
```powershell
$version = "v$(Get-Date -Format 'yyyy.MM.dd.HHmm')"
```

### 修改提交记录数量
修改获取提交信息的命令：
```powershell
$commits = git log --oneline -20 --pretty=format:"- %s (%an)"
```
将 `-20` 改为其他数字

### 修改编译配置
编辑 `build_exe.spec` 文件来调整：
- 包含的文件和目录
- 隐藏导入的模块
- 排除的包
- 图标和版本信息

## 🔍 监控和调试

### 查看构建状态
1. 进入GitHub仓库
2. 点击 "Actions" 标签
3. 查看最新的工作流运行状态

### 常见问题
1. **编译失败** - 检查依赖包是否正确安装
2. **文件缺失** - 确认spec文件中的路径配置
3. **权限问题** - 确保GITHUB_TOKEN有足够权限

### 调试方法
- 查看Actions运行日志
- 本地测试PyInstaller编译
- 检查requirements.txt依赖

## 📋 使用建议

1. **推送前测试** - 确保本地能正常编译运行
2. **合理提交** - 写清楚提交信息，因为会出现在发布日志中
3. **版本管理** - 重要更新可以手动创建标签版本
4. **文件大小** - 注意exe文件大小，避免包含不必要的依赖

## 🎯 下一步优化

可以考虑的改进：
- 添加代码签名避免杀毒软件误报
- 支持多平台编译（Linux、macOS）
- 添加自动化测试
- 集成版本号管理工具
- 添加更详细的发布说明模板
