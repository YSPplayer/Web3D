<template>
  <el-dialog
    v-model="dialogVisible"
    title="系统设置"
    class="config_dialog"
    align-center
    :close-on-click-modal="false"
    @opened="handleOpen"
    @closed="handleClosed"
  >
    <div class="flex_colum_center">
      <el-tabs v-model="activeName" class="config_tab" tab-position="left">
        <el-tab-pane name="model">
          <template #label>
            <span class="config_tab_label">模型管理</span>
          </template>
          <ConfigModel :manager="modelManager" />
        </el-tab-pane>
        <el-tab-pane name="agent">
          <template #label>
            <span class="config_tab_label">工具管理</span>
          </template>
          <ConfigAgent />
        </el-tab-pane>
        <el-tab-pane name="user">
          <template #label>
            <span class="config_tab_label">用户管理</span>
          </template>
          <ConfigUser />
        </el-tab-pane>
      </el-tabs>
      <div class="config_bottom flex_row">
        <el-button :loading="saveconfigLoading" type="primary" @click="saveConfig">
          保存
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import ConfigModel, { useConfigModel } from './configmodel.vue'
import ConfigAgent from './configagent.vue'
import ConfigUser from './configuser.vue'

const activeName = ref('model')
const dialogVisible = ref(false)
const saveconfigLoading = ref(false)
const modelManager = useConfigModel(loading => {
  saveconfigLoading.value = loading
})

watch(
  [dialogVisible, activeName, modelManager.onlineModel],
  ([visible, currentTab, isOnlineModel]) => {
    modelManager.setMetricsPolling(
      visible && currentTab === 'model' && !isOnlineModel,
    )
  },
)

const handleOpen = async () => {
  await modelManager.initialize()
}

const handleClosed = () => {
  modelManager.dispose()
}

const saveConfig = async () => {
  if (activeName.value !== 'model') return
  await modelManager.saveConfig(true)
}

const updateUserModelConfig = async (...args) => {
  return await modelManager.updateUserModelConfig(...args)
}

const openDialog = () => {
  dialogVisible.value = true
}

const closeDialog = () => {
  dialogVisible.value = false
}

defineExpose({
  openDialog,
  closeDialog,
  updateUserModelConfig,
})
</script>

<style>
.config_bottom {
  width: 100%;
}

.config_bottom .el-button {
  width: 100px;
  height: 35px;
  margin-left: auto;
  font-size: 16.5px;
}

.config_tab_label {
  font-size: 1.1rem;
}

.config_tab {
  width: 100%;
}

.el-dialog.config_dialog {
  width: 800px;
}
</style>
