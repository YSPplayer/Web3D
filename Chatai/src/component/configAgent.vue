<template>
<div class="config_agent_container flex_colum">
        <el-button type="primary" class="config_agent_add" @click="handleAddTool()">
        工具新增
        </el-button>
    <el-table v-loading="loading" :data="tableData">
      <el-table-column prop="id" label="序号" align="center" />
      <el-table-column prop="display_name" label="名称" align="center" />
      <el-table-column prop="risk_level" label="风险" align="center">
         <template #default="{ row }"> 
              <el-tag :type="getStatusType(row.risk_level)">
            {{ getStatusTag(row.risk_level) }}
          </el-tag>
         </template>
      </el-table-column>
      <el-table-column label="状态" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_enabled ? 'success' : 'info'">
            {{ row.is_enabled ? '活跃' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
       <el-table-column label="操作" align="center">
        <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleTableView(row)">
            查看详情
            </el-button>
        </template>
       </el-table-column>
    </el-table>
    <div  class="flex_colum_center">
        <el-pagination 
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        @current-change="handleCurrentChange"
        />
    </div>
    <el-dialog
      v-model="detailDialogVisible"
      title="工具详情"
      class="config_agent_detail_dialog"
      align-center
      :close-on-click-modal="false"
      @closed="handleDetailClosed"
    >
      <div v-if="selectedTool" class="agent_tool_detail">
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">序号</span>
          <span class="agent_tool_detail_value">{{ selectedTool.id }}</span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">显示名称</span>
          <span class="agent_tool_detail_value">{{ selectedTool.display_name }}</span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">工具名称</span>
          <span class="agent_tool_detail_value">{{ selectedTool.tools_name }}</span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">风险</span>
          <span class="agent_tool_detail_value">
            <el-tag :type="getStatusType(selectedTool.risk_level)">
              {{ getStatusTag(selectedTool.risk_level) }}
            </el-tag>
          </span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">状态</span>
          <span class="agent_tool_detail_value">
            <el-tag :type="selectedTool.is_enabled ? 'success' : 'info'">
              {{ selectedTool.is_enabled ? '活跃' : '禁用' }}
            </el-tag>
          </span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">创建日期</span>
          <span class="agent_tool_detail_value">{{ selectedTool.created_at }}</span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">修改日期</span>
          <span class="agent_tool_detail_value">{{ selectedTool.updated_at }}</span>
        </div>
        <div class="agent_tool_detail_row agent_tool_description_row">
          <span class="agent_tool_detail_label">描述</span>
          <span class="agent_tool_detail_value">{{ selectedTool.description }}</span>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
</div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ChatAiApi } from '@/api/api'
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedTool = ref(null)
const getStatusType = (risk)=> {
    if(risk === 'low') return 'success'
    if(risk === 'medium') return 'warning'
    return 'danger'
}
const getStatusTag = (risk) => {
    if(risk === 'low') return '低'
    if(risk === 'medium') return '中'
    return '高'
}
const loadAgentTools = async () => {
    loading.value = true
    try {
        const result = await ChatAiApi.getAgentToolsPageApi(
            currentPage.value,
            pageSize.value
        )
        if(result?.code === 200) {
            tableData.value = result.data.items
            total.value = result.data.total
        }
    } finally {
        loading.value = false
    }
}
const handleCurrentChange = (page) => {
    currentPage.value = page
    loadAgentTools()
}
const handleTableView = (row)=> {
    selectedTool.value = row
    detailDialogVisible.value = true
}
const handleDetailClosed = () => {
    selectedTool.value = null
}
const handleAddTool = ()=> {

}
onMounted(() => {
    loadAgentTools()
})
</script>

<style>
.config_agent_add {
  width: 100px;
}
.config_agent_container {
    width: 100%;
    height: 100%;
    gap:1rem;
    margin-bottom: 1rem;
}

.el-dialog.config_agent_detail_dialog {
    width: 540px;
    border-radius: 5px;
}

.agent_tool_detail {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}

.agent_tool_detail_row {
    display: grid;
    grid-template-columns: 6rem minmax(0, 1fr);
    align-items: center;
    min-height: 2.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    /* background-color: var(--el-fill-color-light); */
}

.agent_tool_detail_label {
    color: var(--el-text-color-secondary);
}

.agent_tool_detail_value {
    min-width: 0;
    color: var(--el-text-color-primary);
    overflow-wrap: anywhere;
}

.agent_tool_description_row {
    align-items: start;
}
</style>
