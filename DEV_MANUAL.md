# 开发者手册

本手册为开发者提供参与本项目所需的信息。

## 1. 项目架构

本项目是一个桌面应用程序，采用以下技术栈：

*   **Electron**: 用于构建跨平台的桌面应用框架。
*   **Vue.js**: 用于构建用户界面的前端框架。
*   **Python (Flask)**: 作为后端，处理核心的下载逻辑。
*   **Electron-Forge**: 用于打包和分发应用。

Electron 主进程 (`src/main/main.js`) 负责创建窗口和管理应用的生命周期。渲染器进程 (`src/renderer/`) 使用 Vue.js 构建UI。主进程通过 `preload.js` 脚本向渲染器进程暴露特定的 IPC 通道，以实现安全的通信。Python 后端作为一个独立的 Flask 服务运行，并通过 HTTP 请求与 Electron 应用通信。

## 2. 开发环境设置

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/your-username/Tomato-Novel-Downloader.git
    cd Tomato-Novel-Downloader
    ```

2.  **安装 Node.js 依赖**:
    ```bash
    npm install
    ```

3.  **安装 Python 依赖**:
    ```bash
    pip install -r src/python/requirements.txt
    ```

## 3. 构建与测试

项目包含一套 `npm` 脚本来简化开发流程：

*   `npm start`: 在开发模式下启动应用。
*   `npm run build`: 构建生产版本的应用。
*   `npm run test:unit`: 运行单元测试 (Jest)。
*   `npm run test:e2e`: 运行端到端测试 (Playwright)。
*   `npm test`: 运行所有测试。

## 4. API 文档

### 4.1 IPC 通道 (`preload.js`)

*   `ipcRenderer.invoke('some-channel', ...args)`: 示例通道。

*(请根据 `preload.js` 的实际内容填充)*

### 4.2 Python Flask API

*   **GET /api/download**:
    *   **描述**: 下载指定 URL 的小说。
    *   **参数**: `url` (string, required)。
*   **GET /api/status**:
    *   **描述**: 获取下载任务的状态。
    *   **参数**: `task_id` (string, required)。

*(请根据 `src/python/main.py` 的实际内容填充)*