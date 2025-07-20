<template>
  <div class="about-view">
    <h1>关于</h1>
    <div class="app-info">
      <p>版本: {{ appVersion }}</p>
    </div>
    <div class="update-info">
      <p>更新状态: {{ updateStatus }}</p>
      <button @click="checkForUpdates" :disabled="checkingForUpdate">
        {{ checkingForUpdate ? '正在检查...' : '检查更新' }}
      </button>
      <button v-if="updateDownloaded" @click="restartApp">
        重启并安装
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AboutView',
  data() {
    return {
      appVersion: '加载中...',
      updateStatus: '等待检查',
      updateDownloaded: false,
      checkingForUpdate: false,
    };
  },
  async created() {
    this.appVersion = await window.electron.getAppVersion();
    
    window.electron.onUpdateAvailable(() => {
      this.updateStatus = '发现新版本，正在下载...';
      this.checkingForUpdate = false;
    });

    window.electron.onUpdateDownloaded(() => {
      this.updateStatus = '下载完成，请点击安装。';
      this.updateDownloaded = true;
      this.checkingForUpdate = false;
    });
  },
  methods: {
    checkForUpdates() {
      this.checkingForUpdate = true;
      this.updateStatus = '正在检查更新...';
      window.electron.checkForUpdate();
    },
    restartApp() {
      window.electron.restartApp();
    },
  },
};
</script>

<style scoped>
.about-view {
  padding: 20px;
}
.app-info, .update-info {
  margin-top: 20px;
}
button {
  margin-right: 10px;
}
</style>