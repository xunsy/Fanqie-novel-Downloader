const { app, BrowserWindow, ipcMain, dialog, shell, Tray, Menu, globalShortcut } = require('electron');
const { autoUpdater } = require('electron-updater');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const Store = require('electron-store');
const log = require('electron-log');

// 配置 electron-log
log.transports.file.resolvePath = () => path.join(app.getPath('userData'), 'logs/main.log');
log.transports.file.level = 'info';
log.info('应用启动');

// 开发环境检测
const isDev = process.env.NODE_ENV === 'development';

// 全局变量
let mainWindow;
let pythonProcess;
let tray;
let pythonServiceIdleTimeout; // 用于空闲超时的计时器

// 初始化 electron-store
const store = new Store({
  defaults: {
    downloadPath: app.getPath('downloads'),
    fileType: 'txt',
    history: []
  }
});

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../../assets/icon.png'),
    show: false,
    titleBarStyle: 'default'
  });

  // 加载应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:8080');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
  });

  // 窗口关闭事件
  mainWindow.on('closed', () => {
    mainWindow = null;
    // 关闭Python进程
    if (pythonProcess) {
      pythonProcess.kill();
    }
  });

  // 失去焦点时注销快捷键
  mainWindow.on('blur', () => {
    globalShortcut.unregisterAll();
  });

  // 获得焦点时重新注册快捷键
  mainWindow.on('focus', () => {
    registerShortcuts();
  });
}

// 启动Python后端服务
function startPythonService() {
  // 如果进程已经存在，则不执行任何操作
  if (pythonProcess) {
    log.info('Python服务已在运行中。');
    return;
  }
  
  const pythonPath = isDev
    ? path.join(__dirname, '../python/main.py')
    : path.join(process.resourcesPath, 'python/main.py');
    
  if (!fs.existsSync(pythonPath)) {
    log.error('Python服务文件不存在:', pythonPath);
    dialog.showErrorBox('启动错误', `无法找到Python服务文件: ${pythonPath}`);
    return;
  }

  log.info('正在启动Python服务...');
  pythonProcess = spawn('python', [pythonPath], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    const message = data.toString();
    log.info('Python输出:', message);
    // 假设服务准备就绪时会输出特定消息
    if (message.includes(' * Running on')) {
        mainWindow.webContents.send('python-service-started');
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const errorMessage = data.toString();
    log.error('Python错误:', errorMessage);
  });

  pythonProcess.on('close', (code) => {
    log.info('Python进程退出，代码:', code);
    pythonProcess = null; // 清理进程引用
    mainWindow.webContents.send('python-service-stopped');
  });

  pythonProcess.on('error', (err) => {
    log.error('启动Python进程失败:', err);
    pythonProcess = null;
    dialog.showErrorBox('启动错误', `启动Python服务时发生错误: ${err.message}`);
  });
}

// 确保Python服务正在运行
async function ensurePythonServiceIsRunning() {
  resetIdleTimeout(); // 任何需要服务的活动都应重置超时
  if (!pythonProcess) {
    log.info('Python服务未运行，正在启动...');
    startPythonService();
    // 等待服务启动
    await new Promise(resolve => {
        // 在 preload.js 中，我们需要监听 'python-service-started' 事件，
        // 然后调用 ipcRenderer.send('python-service-started-response')
        ipcMain.once('python-service-started-response', resolve);
        // 设置一个超时以防服务无法启动
        setTimeout(resolve, 5000); // 5秒超时
    });
  }
}

// 关闭Python服务
function stopPythonService() {
  if (pythonProcess) {
    log.info('正在关闭Python服务...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

// 重置空闲计时器
function resetIdleTimeout() {
  if (pythonServiceIdleTimeout) {
    clearTimeout(pythonServiceIdleTimeout);
  }
  // 5分钟后关闭服务
  pythonServiceIdleTimeout = setTimeout(() => {
    log.info('Python服务因空闲超时而关闭。');
    stopPythonService();
  }, 5 * 60 * 1000);
}

// 创建系统托盘
function createTray() {
  const iconPath = path.join(__dirname, '../../assets/icon.png'); // 确保你有这个图标文件
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示/隐藏窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
      },
    },
    {
      label: '退出',
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setToolTip('番茄小说下载器');
  tray.setContextMenu(contextMenu);
}

// 注册快捷键
function registerShortcuts() {
  globalShortcut.register('CommandOrControl+N', () => {
    if (mainWindow) {
      mainWindow.webContents.send('focus-book-id-input');
    }
  });

  globalShortcut.register('CommandOrControl+Q', () => {
    app.quit();
  });
}

// 应用事件处理
app.whenReady().then(() => {
  createWindow();
  // 不再在启动时立即启动Python服务
  // startPythonService();
  createTray();
  registerShortcuts();

  // 启动时检查更新
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  globalShortcut.unregisterAll();
});

// IPC事件处理
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths;
  }
  return null;
});

ipcMain.handle('open-folder', async (event, folderPath) => {
  shell.openPath(folderPath);
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-config', async () => {
  return store.store;
});

ipcMain.handle('set-config', async (event, config) => {
  store.set(config);
  return { success: true };
});

ipcMain.handle('get-history', async () => {
  return store.get('history', []);
});

ipcMain.handle('add-history', async (event, historyEntry) => {
  const history = store.get('history', []);
  history.unshift(historyEntry);
  // 去重，保留最新的记录
  const uniqueHistory = history.filter((item, index, self) =>
    index === self.findIndex((t) => (
      t.bookId === item.bookId
    ))
  );
  store.set('history', uniqueHistory);
  return { success: true };
});

ipcMain.handle('clear-history', async () => {
  store.set('history', []);
  return { success: true };
});

// 自动更新事件
autoUpdater.on('checking-for-update', () => {
  log.info('检查更新中...');
});

autoUpdater.on('update-available', (info) => {
  log.info('发现新版本:', info);
  mainWindow.webContents.send('update-available');
});

autoUpdater.on('update-not-available', () => {
  log.info('当前已是最新版本');
});

autoUpdater.on('error', (err) => {
  log.error('更新错误:', err);
});

autoUpdater.on('download-progress', (progressObj) => {
  log.info('下载进度:', progressObj);
  mainWindow.webContents.send('download-progress', progressObj);
});

autoUpdater.on('update-downloaded', () => {
  log.info('更新下载完成');
  mainWindow.webContents.send('update-downloaded');
});

ipcMain.on('restart-app', () => {
  autoUpdater.quitAndInstall();
});

ipcMain.on('check-for-update', () => {
  log.info('手动检查更新');
  if (!isDev) {
    autoUpdater.checkForUpdates();
  }
});

// 和Python后端的通信
const API_BASE_URL = 'http://127.0.0.1:5001'; // 修正端口号

ipcMain.handle('start-download', async (event, { bookId }) => {
  log.info(`收到下载请求, bookId: ${bookId}`);
  if (!bookId) {
    log.error('下载请求失败: Book ID 不能为空');
    return { success: false, message: 'Book ID 不能为空' };
  }
  
  await ensurePythonServiceIsRunning();

  try {
    const downloadPath = store.get('downloadPath');
    const fileType = store.get('fileType');

    log.info(`向后端发送下载请求, bookId: ${bookId}, downloadPath: ${downloadPath}, fileType: ${fileType}`);
    
    const response = await axios.post(`${API_BASE_URL}/api/download`, {
      book_id: bookId,
      download_path: downloadPath,
      file_type: fileType
    });

    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = error.response ? error.response.data.error : error.message;
    log.error(`下载书籍 ${bookId} 失败:`, errorMessage);
    return { success: false, message: `请求后端服务失败: ${errorMessage}` };
  }
});

ipcMain.handle('check-status', async () => {
  await ensurePythonServiceIsRunning();
  try {
    const response = await axios.get(`${API_BASE_URL}/api/status`);
    // 如果后端返回错误状态，也记录一下
    if (response.data.status === 'error') {
      log.warn(`后端报告错误: ${response.data.error_message}`);
    }
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = error.response ? error.response.data.error : error.message;
    log.error('检查状态失败:', errorMessage);
    return { success: false, message: `请求后端服务失败: ${errorMessage}` };
  }
});