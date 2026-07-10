<template>
  <el-dialog
    align-center
    v-model="visible"
    :title="title"
    @close="handleClose"
    width="10%"
  >
    <div class="colflex">
      <div class="rowflex dialog-content">
        <label>样本数量</label>
        <el-slider v-model="sampleCount" class="count-slider" :min="1" :max="30"></el-slider>
        <label>{{ sampleCount }}</label>
      </div>
      <el-button type="primary" class="confirm-button" @click="handleconfirm">确认</el-button>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { grayImageApi } from '@/api/grayImageApi'
import { ElMessage } from 'element-plus'
const emit = defineEmits(['emitSetTableData'])
defineOptions({
  name: 'SampleCountDialog'
})

const sampleCount = ref(1)
const visible = ref(false)
const title = ref('')

const handleOpen = () => {
  visible.value = true
}

const handleClose = () => {
  visible.value = false
}

const handleconfirm = async () => {
  try {
    const result = await grayImageApi.generateGrayDatas(sampleCount.value)
    emit('emitSetTableData', result.data)
    ElMessage.success('样本数据生成成功！')
    handleClose()
  } catch (error) {
    ElMessage.error('样本数据生成失败！')
  }
}

defineExpose({
  handleOpen
})
</script>

<style scoped>
.dialog-content {
  align-items: center;
  justify-content: center;
}

.count-slider {
  margin-left: 10px;
  margin-right: 10px;
  --el-slider-main-bg-color: #3b82f6;
  --el-slider-runway-bg-color: #dbe3ef;
  --el-slider-height: 4px;
  --el-slider-button-size: 12px;
  --el-slider-button-wrapper-size: 24px;
  --el-slider-button-wrapper-offset: -10px;
}

.confirm-button {
  width: 50%;
  margin-left: 25%;
}

:deep(.count-slider .el-slider__bar) {
  border-radius: 999px;
}

:deep(.count-slider .el-slider__button) {
  border-width: 1px;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.18);
}

:deep(.count-slider .el-slider__button:hover),
:deep(.count-slider .el-slider__button.hover),
:deep(.count-slider .el-slider__button.dragging) {
  transform: scale(1.1);
}

label {
  text-align: center;
  white-space: nowrap;
  flex-shrink: 0;
}
</style>
