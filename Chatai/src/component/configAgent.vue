<template>
<div class="config_agent_container flex_colum">
    <el-table :data="tableData">
      <el-table-column prop="id" label="序号" align="center" />
      <el-table-column prop="display_name" label="名称" align="center" />
      <el-table-column prop="risk" label="风险" align="center">
         <template #default="{ row }"> 
              <el-tag :type="getStatusType(row.risk)">
            {{ getStatusTag(row.risk) }}
          </el-tag>
         </template>
      </el-table-column>
      <el-table-column label="状态" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '活跃' : '禁用' }}
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
            <el-tag :type="getStatusType(selectedTool.risk)">
              {{ getStatusTag(selectedTool.risk) }}
            </el-tag>
          </span>
        </div>
        <div class="agent_tool_detail_row">
          <span class="agent_tool_detail_label">状态</span>
          <span class="agent_tool_detail_value">
            <el-tag :type="selectedTool.status === 'active' ? 'success' : 'info'">
              {{ selectedTool.status === 'active' ? '活跃' : '禁用' }}
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
//  @current-change="handleCurrentChange"
import { ref } from 'vue'
const tableData =  [
  { id: 1, tools_name: 'get_current_time', display_name: '获取当前时间', risk: 'low', status: 'active', created_at: '2026-09-01 09:10:00', updated_at: '2026-09-01 09:10:00', description: '获取当前操作系统的日期、时间、时区和时间戳。' },
  { id: 2, tools_name: 'file_stat', display_name: '查看文件信息', risk: 'low', status: 'inactive', created_at: '2026-09-01 09:12:00', updated_at: '2026-09-02 08:20:00', description: '查询指定文件或目录的类型、大小和修改时间。' },
  { id: 3, tools_name: 'find_files', display_name: '查找文件', risk: 'medium', status: 'active', created_at: '2026-09-01 09:15:00', updated_at: '2026-09-02 08:30:00', description: '在指定目录中按照文件名规则查找文件。' },
  { id: 4, tools_name: 'kill_process', display_name: '结束进程', risk: 'low', status: 'active', created_at: '2026-09-01 09:18:00', updated_at: '2026-09-02 08:40:00', description: '根据进程编号结束指定进程。' },
  { id: 5, tools_name: 'ping_host', display_name: 'Ping 主机', risk: 'high', status: 'inactive', created_at: '2026-09-01 09:20:00', updated_at: '2026-09-02 08:50:00', description: '检测指定主机当前是否能够通过网络连接。' },
]
const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
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
const handleTableView = (row)=> {
    selectedTool.value = row
    detailDialogVisible.value = true
}
const handleDetailClosed = () => {
    selectedTool.value = null
}
</script>

<style>

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
