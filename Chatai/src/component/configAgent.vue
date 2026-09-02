<template>
<div class="config_agent_container flex_colum">
    <el-table :data="tableData">
      <el-table-column prop="id" label="序号" align="center" />
      <el-table-column prop="toolname" label="工具名称" align="center" />
      <el-table-column prop="risk" label="风险" align="center">
         <template #default="{ row }"> 
              <el-tag :type="getStatusType(row.risk)">
            {{ getStatusTag(row.risk) }}
          </el-tag>
         </template>
      </el-table-column>
      <el-table-column label="状态" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
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
</div>
</template>

<script setup>
//  @current-change="handleCurrentChange"
import { ref, onMounted } from 'vue'
const tableData =  [
  { id: 1, toolname: '获取当前时间', risk: 'low', status: 'active' },
  { id: 2, toolname: '查看文件信息',  risk: 'low', status: 'inactive' },
  { id: 3, toolname: '查找文件',  risk: 'medium', status: 'active' },
  { id: 4, toolname: '结束进程',  risk: 'low', status: 'active' },
  { id: 5, toolname: 'Ping 主机', risk: 'high', status: 'inactive' },
]
const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
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
const handleTableView = ()=> {

}
</script>

<style>

.config_agent_container {
    width: 100%;
    height: 100%;
    gap:1rem;
    margin-bottom: 1rem;
}
</style>