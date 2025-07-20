<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>番茄小说下载器</h1>
            <span class="version">v{{ appVersion }}</span>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="200px" class="app-sidebar">
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="download">
              <el-icon><Download /></el-icon>
              <span>下载小说</span>
            </el-menu-item>
            <el-menu-item index="history">
              <el-icon><Clock /></el-icon>
              <span>下载历史</span>
            </el-menu-item>
            <el-menu-item index="settings">
              <el-icon><Setting /></el-icon>
              <span>设置</span>
            </el-menu-item>
            <el-menu-item index="about">
              <el-icon><InfoFilled /></el-icon>
              <span>关于</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <!-- 下载页面 -->
          <div v-if="activeMenu === 'download'" class="page-content">
            <DownloadView />
          </div>
          
          <!-- 历史页面 -->
          <div v-else-if="activeMenu === 'history'" class="page-content">
            <HistoryView />
          </div>
          
          <!-- 设置页面 -->
          <div v-else-if="activeMenu === 'settings'" class="page-content">
            <SettingsView />
          </div>
          
          <!-- 关于页面 -->
          <div v-else-if="activeMenu === 'about'" class="page-content">
            <AboutView />
          </div>
        </el-main>
      </el-container>
    </el-container>

  </div>
</template>

<script>
import { ref, onMounted, defineAsyncComponent } from 'vue';
import DownloadView from './components/DownloadView.vue';

// 异步加载非首屏组件
const HistoryView = defineAsyncComponent(() => import('./components/HistoryView.vue'));
const SettingsView = defineAsyncComponent(() => import('./components/SettingsView.vue'));
const AboutView = defineAsyncComponent(() => import('./components/AboutView.vue'));

export default {
  name: 'App',
  components: {
    DownloadView,
    HistoryView,
    SettingsView,
    AboutView
  },
  setup() {
    const activeMenu = ref('download');
    const appVersion = ref('加载中...');

    // 菜单选择处理
    const handleMenuSelect = (index) => {
      activeMenu.value = index;
    };

    // 初始化
    onMounted(async () => {
      try {
        appVersion.value = await window.electron.getAppVersion();
      } catch (error) {
        console.error('获取应用版本失败:', error);
      }
    });

    return {
      activeMenu,
      appVersion,
      handleMenuSelect,
    };
  }
};
</script>

<style scoped>
.app-container {
  height: 100vh;
  background: #f5f5f5;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.version {
  font-size: 12px;
  opacity: 0.8;
  margin-left: 10px;
}

.app-sidebar {
  background: white;
  box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}

.sidebar-menu {
  border: none;
  height: 100%;
}

.app-main {
  padding: 20px;
  background: #f5f5f5;
}

.page-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  height: calc(100vh - 140px);
  overflow-y: auto;
}
</style>