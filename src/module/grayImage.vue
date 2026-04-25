<template>
  <div class="right_container colflex">
    <el-button class="sample-btn" type="primary" @click="openSampleCountDialog">生成样本</el-button>
    <SampleCountDialog ref="sampleCountDialogRef" @emitSetTableData="setTableData" />
    <div class="train_container colflex">
      <el-table
        :data="tableData"
        border
        class="gray-image-table"
        style="width: 100%"
        :cell-style="{ textAlign: 'center', verticalAlign: 'middle', whiteSpace: 'nowrap' }"
        :header-cell-style="{ textAlign: 'center', verticalAlign: 'middle', whiteSpace: 'nowrap' }"
      >
        <el-table-column prop="id" label="序号" width="auto" align="center" />
        <el-table-column prop="image" label="图像" width="180" align="center">
          <template #default="{ row }">
            <div class="image-cell">
              <img :src="row.image"  class="table-image" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="数值" width="auto" align="center" />
        <el-table-column prop="createdAt" label="创建日期" width="180" align="center" />
      </el-table>
      <div class="rowflex flexcenter" style="margin-top: 10px;">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      background
      @current-change="handleCurrentChange"
    />
    <label style="display: block; text-align: center; margin-left: 10px; " >页</label>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref,onMounted } from 'vue'
import SampleCountDialog from '@/component/samplecountdialog.vue'
import { grayImageApi } from '@/api/grayImageApi'
const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
const tableData = ref<any[]>([])
const sampleCountDialogRef = ref()
//更新表格数据
const updateTableData = async () => {
  const params = {
    pageNum: currentPage.value,
    pageSize: pageSize.value
  }
  const result = await grayImageApi.getGrayDatasByPage(params)
  setTableData(result.data)
}
onMounted(async ()=>{
  //获取数据库存放的样本总量
  const result = await grayImageApi.getGrayDataTotalCount()
  total.value = result.data
  await updateTableData()
})
const openSampleCountDialog = () => {
  sampleCountDialogRef.value.handleOpen()
}
const handleCurrentChange = async (page: number) => {
  currentPage.value = page
  await updateTableData()
}
const setTableData = (data: any) => {
  tableData.value = data.map((edata: any, index: number) => ({
    id: index + 1,
    image: edata.imgPath,
    value: edata.imgValue,
    createdAt: edata.createTime ? new Date(edata.createTime).toLocaleString() : ''
  }))
}
</script>

<style scoped>
.sample-btn {
  align-self: flex-start;
  width: auto;
  margin: 10px;
}

.gray-image-table :deep(.cell) {
  white-space: nowrap;
}

.image-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}

.table-image {
  display: block;
  width: auto;
  height: auto;
  max-width: 160px;
  max-height: 120px;
  object-fit: contain;
  border-radius: 6px;
}
</style>
