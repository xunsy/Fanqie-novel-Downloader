<template>
  <div class="settings-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>应用设置</span>
        </div>
      </template>
      
      <el-form :model="settings" label-width="150px" size="large">
        <el-divider content-position="left">下载设置</el-divider>
        
        <el-form-item label="默认保存路径">
          <el-input
            v-model="settings.downloadPath"
            placeholder="选择默认保存路径"
            readonly
          >
            <template #append>
              <el-button @click="selectPath">选择文件夹</el-button>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="默认文件格式">
          <el-radio-group v-model="settings.fileType">
            <el-radio label="txt">TXT格式</el-radio>
            <el-radio label="epub">EPUB格式</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

export default {
  name: 'SettingsView',
  setup() {
    const settings = ref({
      downloadPath: '',
      fileType: 'txt',
    });

    // 选择路径
    const selectPath = async () => {
      try {
        const path = await window.electronAPI.selectFolder();
        if (path) {
          settings.value.downloadPath = path;
        }
      } catch (error) {
        ElMessage.error('选择文件夹失败');
      }
    };

    // 加载设置
    const loadSettings = async () => {
      try {
        const config = await window.electronAPI.getConfig();
        if (config) {
          settings.value = config;
        }
      } catch (error) {
        ElMessage.error('加载设置失败');
      }
    };

    // 保存设置
    const saveSettings = async () => {
      try {
        await window.electronAPI.setConfig(settings.value);
        ElMessage.success('设置保存成功');
      } catch (error) {
        ElMessage.error('保存设置失败');
      }
    };

    // 初始化
    onMounted(() => {
      loadSettings();
    });

    return {
      settings,
      selectPath,
      saveSettings,
    };
  }
};
</script>

<style scoped>
.settings-view {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.el-divider {
  margin: 30px 0 20px 0;
}
</style>