<template>
  <div class="history-view">
    <h2>下载历史</h2>
    <div class="toolbar">
      <el-button @click="loadHistory" :icon="Refresh" circle></el-button>
      <el-button type="danger" @click="confirmClearHistory" :disabled="history.length === 0">
        清空历史记录
      </el-button>
    </div>
        <div class="history-list" v-if="history.length > 0">
          <RecycleScroller
            class="scroller"
            :items="history"
            :item-size="80"
            key-field="bookId"
            v-slot="{ item }"
          >
            <div class="history-item">
              <div class="item-info">
                <h3 class="item-title">{{ item.title }}</h3>
                <p class="item-meta">ID: {{ item.bookId }}</p>
                <p class="item-meta">下载于: {{ new Date(item.timestamp).toLocaleString() }}</p>
              </div>
              <div class="item-actions">
                <el-button type="primary" size="small" @click="redownload(item)">
                  重新下载
                </el-button>
              </div>
            </div>
          </RecycleScroller>
        </div>
        <el-empty description="暂无下载历史" v-if="!loading && history.length === 0"></el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';

const history = ref([]);
const loading = ref(false);

const loadHistory = async () => {
  loading.value = true;
  try {
    const historyData = await window.electronAPI.getHistory();
    history.value = historyData;
  } catch (error) {
    ElMessage.error('加载历史记录失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const confirmClearHistory = () => {
  ElMessageBox.confirm(
    '确定要清空所有下载历史记录吗？此操作不可逆！',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    await clearHistory();
  }).catch(() => {
    // 用户取消
  });
};

const clearHistory = async () => {
  const result = await window.electronAPI.clearHistory();
  if (result.success) {
    ElMessage.success('历史记录已清空');
    await loadHistory();
  } else {
    ElMessage.error('清空历史记录失败');
  }
};

const redownload = async (item) => {
  try {
    ElMessage.info(`开始重新下载: ${item.title}`);
    await window.electronAPI.startDownload(item.bookId, item.title);
  } catch (error) {
    ElMessage.error(`重新下载失败: ${error.message}`);
  }
};

onMounted(() => {
  loadHistory();
});
</script>

<style scoped>
.history-view {
  padding: 20px;
}
.toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}
.history-list {
  height: calc(100vh - 220px); /* Adjust height as needed */
}
.scroller {
  height: 100%;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
  height: 80px;
}
.item-info .item-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 5px 0;
}
.item-info .item-meta {
  font-size: 12px;
  color: #909399;
  margin: 0;
}
</style>