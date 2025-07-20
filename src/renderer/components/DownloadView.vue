<template>
  <div class="download-view">
    <el-card class="download-form-card">
      <template #header>
        <div class="card-header">
          <span>下载小说</span>
        </div>
      </template>
      
      <el-form :model="downloadForm" label-width="100px" size="large">
        <el-form-item label="小说ID" required>
                    <el-input
                      ref="bookIdInput"
                      v-model="downloadForm.bookId"
                      placeholder="请输入番茄小说的ID"
                      clearable
                    />
          <div class="form-tip">
            提示：可以从小说页面URL中获取ID，例如：fanqienovel.com/page/123456789
          </div>
        </el-form-item>
        
        <el-form-item label="保存路径" required>
          <el-input
            v-model="downloadForm.savePath"
            placeholder="选择保存路径"
            readonly
          >
            <template #append>
              <el-button @click="selectSavePath">选择文件夹</el-button>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="文件格式">
          <el-radio-group v-model="downloadForm.format">
            <el-radio label="txt">TXT格式</el-radio>
            <el-radio label="epub">EPUB格式</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="startDownload"
            :loading="downloading"
            :disabled="!canDownload"
            size="large"
          >
            {{ downloading ? '下载中...' : '开始下载' }}
          </el-button>
          <el-button 
            v-if="downloading"
            @click="cancelDownload"
            size="large"
          >
            取消下载
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 下载进度区域 -->
    <el-card v-if="showProgress" class="progress-card">
      <template #header>
        <div class="card-header">
          <span>下载进度</span>
        </div>
      </template>
      
      <div class="progress-content">
        <div class="book-info" v-if="bookInfo">
          <h3>{{ bookInfo.name }}</h3>
          <p>作者：{{ bookInfo.author }}</p>
          <p>简介：{{ bookInfo.description }}</p>
        </div>
        
        <div class="progress-stats">
          <el-progress 
            :percentage="progressPercentage" 
            :status="progressStatus"
            :stroke-width="8"
          />
          <div class="stats-row">
            <span>进度：{{ downloadedChapters }}/{{ totalChapters }} 章节</span>
            <span>状态：{{ statusText }}</span>
          </div>
        </div>
        
        <div class="chapter-list-container" v-if="chapters.length > 0">
          <h4>章节状态</h4>
                      <RecycleScroller
                        class="scroller"
                        :items="chapters"
                        :item-size="40"
                        key-field="title"
                        v-slot="{ item }"
                      >
                        <div class="chapter-item" :class="`status-${item.status}`">
                          <span class="chapter-title">{{ item.title }}</span>
                          <span class="chapter-status">{{ getStatusText(item.status) }}</span>
                        </div>
                      </RecycleScroller>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onUnmounted, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
  name: 'DownloadView',
  setup() {
    const bookIdInput = ref(null);
    const downloadForm = ref({
      bookId: '',
      savePath: '',
      format: 'txt'
    });

    const downloading = ref(false);
    const showProgress = ref(false);
    const bookInfo = ref(null);
    const downloadedChapters = ref(0);
    const totalChapters = ref(0);
    const chapters = ref([]);
    const statusText = ref('准备中...');
    let statusInterval = null;

    // 计算属性
    const canDownload = computed(() => {
      return downloadForm.value.bookId.trim() && downloadForm.value.savePath.trim() && !downloading.value;
    });

    const progressPercentage = computed(() => {
      if (totalChapters.value === 0) return 0;
      return Math.round((downloadedChapters.value / totalChapters.value) * 100);
    });

    const progressStatus = computed(() => {
      if (statusText.value === '错误') return 'exception';
      if (downloading.value) return '';
      if (progressPercentage.value === 100) return 'success';
      return '';
    });

    // 清理定时器
    const stopStatusCheck = () => {
      if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
      }
    };

    // 重置UI状态
    const resetUI = () => {
      downloading.value = false;
      showProgress.value = false;
      bookInfo.value = null;
      downloadedChapters.value = 0;
      totalChapters.value = 0;
      chapters.value = [];
      statusText.value = '准备中...';
    };

    // 选择保存路径
    const selectSavePath = async () => {
      try {
        const path = await window.electronAPI.selectFolder();
        if (path) {
          downloadForm.value.savePath = path[0];
        }
      } catch (error) {
        ElMessage.error('选择文件夹失败');
      }
    };

    // 检查状态
    const checkStatus = async () => {
      try {
        const response = await window.electronAPI.checkStatus();
        
        if (response.success) {
            const status = response.data;
            downloadedChapters.value = status.downloaded_chapters;
            totalChapters.value = status.total_chapters;
            statusText.value = getStatusText(status.status);
            
            if (status.book_info) {
              bookInfo.value = status.book_info;
            }
            
            if (status.chapters) {
              chapters.value = status.chapters;
            }

            if (status.status === 'completed') {
                downloading.value = false;
                stopStatusCheck();
                ElMessage.success(`下载完成！文件保存在：${status.filePath}`);
            } else if (status.status === 'error') {
                stopStatusCheck();
                ElMessageBox.alert(status.error_message || '发生未知错误', '下载失败', {
                  confirmButtonText: '好的',
                  type: 'error',
                });
                resetUI(); // 重置UI
            }
        } else {
            stopStatusCheck();
            ElMessageBox.alert(response.message, '通信错误', {
              confirmButtonText: '好的',
              type: 'error',
            });
            resetUI();
        }
      } catch (error) {
        stopStatusCheck();
        ElMessageBox.alert(error.message, '前端错误', {
          confirmButtonText: '好的',
          type: 'error',
        });
        resetUI();
      }
    };

    // 开始下载
    const startDownload = async () => {
      if (!canDownload.value) {
        ElMessage.warning('请填写完整的下载信息或等待当前任务完成');
        return;
      }

      downloading.value = true;
      showProgress.value = true;
      statusText.value = '正在启动下载...';
      downloadedChapters.value = 0;
      totalChapters.value = 0;
      chapters.value = [];
      bookInfo.value = null;

      try {
        const result = await window.electronAPI.startDownload({ bookId: downloadForm.value.bookId });
        if (result.success) {
          ElMessage.success('下载任务已启动');
          stopStatusCheck();
          statusInterval = setInterval(checkStatus, 1500); // 1.5秒查询一次
        } else {
          throw new Error(result.message || '下载启动失败');
        }
      } catch (error) {
        ElMessageBox.alert(error.message, '启动失败', {
          confirmButtonText: '好的',
          type: 'error',
        });
        resetUI();
      }
    };

    // 取消下载 (这里暂时没有后端实现，所以只是前端停止)
    const cancelDownload = () => {
        stopStatusCheck();
        resetUI();
        ElMessage.info('下载已取消');
    };

    // 组件卸载时清理定时器
    onMounted(() => {
      window.electron.onFocusBookIdInput(() => {
        if (bookIdInput.value) {
          bookIdInput.value.focus();
        }
      });
    });

    onUnmounted(() => {
      stopStatusCheck();
    });

    const getStatusText = (status) => {
      const map = {
        idle: '空闲',
        downloading: '下载中',
        completed: '已完成',
        error: '错误',
        pending: '排队中',
        failed: '失败'
      };
      return map[status] || status;
    };

    return {
      bookIdInput,
      downloadForm,
      downloading,
      showProgress,
      bookInfo,
      downloadedChapters,
      totalChapters,
      chapters,
      statusText,
      canDownload,
      progressPercentage,
      progressStatus,
      selectSavePath,
      startDownload,
      cancelDownload,
      getStatusText
    };
  }
};
</script>

<style scoped>
.download-view {
  max-width: 800px;
  margin: 0 auto;
}

.download-form-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.progress-card {
  margin-top: 20px;
}

.progress-content {
  padding: 10px 0;
}

.book-info {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 6px;
}

.book-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.book-info p {
  margin: 5px 0;
  color: #606266;
}

.progress-stats {
  margin-bottom: 15px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
}

.current-chapter p {
  margin: 0;
  color: #1890ff;
  font-weight: 500;
}

.chapter-list-container {
  margin-top: 20px;
  height: 300px;
}
.scroller {
  height: 100%;
}
.chapter-list-container h4 {
  margin-bottom: 10px;
  color: #303133;
}
.chapter-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 5px;
  font-size: 14px;
  transition: background-color 0.3s;
}
.chapter-title {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 20px;
}
.chapter-status {
  font-weight: 500;
}

/* Status Colors */
.status-pending {
  background-color: #f4f4f5;
  color: #909399;
}
.status-downloading {
  background-color: #ecf5ff;
  color: #409eff;
}
.status-completed {
  background-color: #f0f9eb;
  color: #67c23a;
}
.status-failed {
  background-color: #fef0f0;
  color: #f56c6c;
}
</style>