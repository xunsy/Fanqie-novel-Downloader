const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electron', {
  // 文件系统操作
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  openFolder: (path) => ipcRenderer.invoke('open-folder', path),
  
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 下载相关
  startDownload: (bookId, title) => ipcRenderer.invoke('start-download', { bookId, title }),
  checkStatus: () => ipcRenderer.invoke('check-status'),
  cancelDownload: () => ipcRenderer.invoke('cancel-download'),
  
  // 配置管理
  getConfig: () => ipcRenderer.invoke('get-config'),
  setConfig: (config) => ipcRenderer.invoke('set-config', config),
  
  // 历史记录
  getHistory: () => ipcRenderer.invoke('get-history'),
  addHistory: (historyEntry) => ipcRenderer.invoke('add-history', historyEntry),
  clearHistory: () => ipcRenderer.invoke('clear-history'),
  
  // 更新相关
  checkForUpdate: () => ipcRenderer.send('check-for-update'),
  restartApp: () => ipcRenderer.send('restart-app'),
  
  // 事件监听
  onDownloadProgress: (callback) => {
    ipcRenderer.on('download-progress', callback);
    return () => ipcRenderer.removeListener('download-progress', callback);
  },
  
  onDownloadComplete: (callback) => {
    ipcRenderer.on('download-complete', callback);
    return () => ipcRenderer.removeListener('download-complete', callback);
  },
  
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update-available', callback);
    return () => ipcRenderer.removeListener('update-available', callback);
  },
  
  onUpdateDownloaded: (callback) => {
    ipcRenderer.on('update-downloaded', callback);
    return () => ipcRenderer.removeListener('update-downloaded', callback);
  },
  
  // Python服务状态
  onPythonServiceStarted: (callback) => {
    const listener = (event, ...args) => {
        ipcRenderer.send('python-service-started-response');
        callback(event, ...args);
    };
    ipcRenderer.on('python-service-started', listener);
    return () => ipcRenderer.removeListener('python-service-started', listener);
  },

  onPythonServiceStopped: (callback) => {
    ipcRenderer.on('python-service-stopped', callback);
    return () => ipcRenderer.removeListener('python-service-stopped', callback);
  },

  onFocusBookIdInput: (callback) => {
    ipcRenderer.on('focus-book-id-input', callback);
    return () => ipcRenderer.removeListener('focus-book-id-input', callback);
  }
});