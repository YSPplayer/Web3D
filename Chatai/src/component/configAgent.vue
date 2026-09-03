<template>
<div class="config_agent_container flex_colum">
        <el-button type="primary" class="config_agent_add" @click="handleAddTool">
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
          <el-switch
            v-if="row.can_update"
            :model-value="row.is_enabled"
            :loading="pendingToolIds.has(row.id)"
            inline-prompt
            active-text="开"
            inactive-text="关"
            active-color="#67c23a"
            inactive-color="#909399"
            @change="(value) => handleToolStateChange(row, value)"
          />
          <el-tag v-else :type="row.is_enabled ? 'success' : 'info'">
              {{ row.is_enabled ? '活跃' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
       <el-table-column label="操作" align="center">
        <template #default="{ row }">
          <div class="agent_tool_actions">
            <el-button type="primary" size="small" @click="handleTableView(row)">
            查看详情
            </el-button>
            <el-button
              v-if="row.can_delete"
              type="danger"
              plain
              size="small"
              :loading="pendingToolIds.has(row.id)"
              @click="handleDeleteTool(row)"
            >
              删除
            </el-button>
          </div>
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
    <el-dialog
      v-model="addDialogVisible"
      title="新增 Agent 工具"
      class="config_agent_add_dialog"
      align-center
      :before-close="handleAddBeforeClose"
      :close-on-click-modal="false"
      :close-on-press-escape="!uploading"
      :show-close="!uploading"
      @closed="resetAddForm"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-width="90px"
      >
        <el-form-item label="工具名称" prop="tools_name">
          <el-input
            v-model="addForm.tools_name"
            maxlength="64"
            placeholder="例如：count_directories"
            :disabled="uploading"
          />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input
            v-model="addForm.display_name"
            maxlength="80"
            placeholder="请输入界面显示名称"
            :disabled="uploading"
          />
        </el-form-item>
        <el-form-item label="运行平台" prop="platform">
          <el-select
            v-model="addForm.platform"
            class="agent_tool_platform"
            :disabled="uploading"
          >
            <el-option label="全部平台" value="all" />
            <el-option label="Windows" value="windows" />
            <el-option label="Linux" value="linux" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具描述" prop="description">
          <el-input
            v-model="addForm.description"
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            resize="none"
            placeholder="描述工具能力，供 Agent 判断何时调用"
            :disabled="uploading"
          />
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload
            ref="uploadRef"
            class="agent_tool_upload"
            accept=".py,text/x-python"
            :auto-upload="false"
            :limit="1"
            :disabled="uploading"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleFileExceed"
          >
            <el-button :disabled="uploading">选择 .py 文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <div
        v-if="addErrorMessage"
        class="agent_tool_error"
        role="alert"
      >
        {{ addErrorMessage }}
      </div>
      <AgentToolExample
        :example="toolExample"
        :loading="exampleLoading"
      />
      <template #footer>
        <el-button :disabled="uploading" @click="addDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="uploading" @click="submitAddTool">
          上传并校验
        </el-button>
      </template>
    </el-dialog>
</div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatAiApi } from '@/api/api'
import AgentToolExample from '@/component/agent/AgentToolExample.vue'
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedTool = ref(null)
const addDialogVisible = ref(false)
const uploading = ref(false)
const uploadFile = ref(null)
const uploadRef = ref(null)
const addFormRef = ref(null)
const addErrorMessage = ref('')
const toolExample = ref(null)
const exampleLoading = ref(false)
const pendingToolIds = ref(new Set())
const addForm = reactive({
    tools_name: '',
    display_name: '',
    description: '',
    platform: 'all'
})
const addFormRules = {
    tools_name: [
        { required: true, message: '请输入工具名称', trigger: 'blur' },
        {
            pattern: /^[a-z][a-z0-9_]{2,63}$/,
            message: '请输入3-64位小写字母、数字或下划线，并以字母开头',
            trigger: 'blur'
        }
    ],
    display_name: [
        { required: true, message: '请输入显示名称', trigger: 'blur' }
    ],
    description: [
        { required: true, message: '请输入工具描述', trigger: 'blur' }
    ],
    platform: [
        { required: true, message: '请选择运行平台', trigger: 'change' }
    ]
}
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
            tableData.value = Array.isArray(result.data?.items)
                ? result.data.items
                : []
            total.value = Number(result.data?.total || 0)
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
    addErrorMessage.value = ''
    addDialogVisible.value = true
    void loadToolExample()
}
const loadToolExample = async () => {
    if(toolExample.value || exampleLoading.value) return
    exampleLoading.value = true
    try {
        const result = await ChatAiApi.getAgentToolExampleApi()
        if(result?.code === 200) {
            toolExample.value = result.data
        }
    } finally {
        exampleLoading.value = false
    }
}
const setToolPending = (toolId, pending) => {
    const nextIds = new Set(pendingToolIds.value)
    if(pending) {
        nextIds.add(toolId)
    } else {
        nextIds.delete(toolId)
    }
    pendingToolIds.value = nextIds
}
const handleToolStateChange = async (row, value) => {
    if(pendingToolIds.value.has(row.id)) return
    const nextState = Boolean(value)
    setToolPending(row.id, true)
    try {
        const result = await ChatAiApi.updateAgentToolStateApi(row.id, nextState)
        if(result?.code === 200) {
            row.is_enabled = Boolean(result.data?.is_enabled)
            if(selectedTool.value?.id === row.id) {
                selectedTool.value = { ...selectedTool.value, ...result.data }
            }
            ElMessage.success(row.is_enabled ? '工具已启用' : '工具已禁用')
        }
    } finally {
        setToolPending(row.id, false)
    }
}
const handleDeleteTool = async (row) => {
    if(pendingToolIds.value.has(row.id)) return
    try {
        await ElMessageBox.confirm(
            `是否删除工具“${row.display_name}”？`,
            '删除工具',
            {
                confirmButtonText: '删除',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )
    } catch {
        return
    }

    setToolPending(row.id, true)
    try {
        const result = await ChatAiApi.deleteAgentToolApi(row.id)
        if(result?.code === 200) {
            ElMessage.success('工具删除成功')
            if(tableData.value.length === 1 && currentPage.value > 1) {
                currentPage.value -= 1
            }
            await loadAgentTools()
        }
    } finally {
        setToolPending(row.id, false)
    }
}
const handleFileChange = (file) => {
    const rawFile = file?.raw
    if(!rawFile) {
        uploadFile.value = null
        return
    }
    if(!rawFile.name.toLowerCase().endsWith('.py')) {
        addErrorMessage.value = '只能上传 .py 文件'
        uploadRef.value?.clearFiles()
        uploadFile.value = null
        return
    }
    if(rawFile.size > 256 * 1024) {
        addErrorMessage.value = '工具文件不能超过 256 KiB'
        uploadRef.value?.clearFiles()
        uploadFile.value = null
        return
    }
    uploadFile.value = rawFile
    addErrorMessage.value = ''
}
const handleFileRemove = () => {
    uploadFile.value = null
}
const handleFileExceed = () => {
    addErrorMessage.value = '一次只能上传一个 Python 文件'
}
const submitAddTool = async () => {
    if(uploading.value) return
    addErrorMessage.value = ''
    try {
        await addFormRef.value?.validate()
    } catch {
        addErrorMessage.value = '请先完成必填信息并检查工具名称格式'
        return
    }
    if(!uploadFile.value) {
        addErrorMessage.value = '请选择需要上传的 Python 文件'
        return
    }

    uploading.value = true
    try {
        const result = await ChatAiApi.uploadAgentToolApi({
            file: uploadFile.value,
            tools_name: addForm.tools_name.trim(),
            display_name: addForm.display_name.trim(),
            description: addForm.description.trim(),
            platform: addForm.platform
        })
        if(result?.code === 200) {
            ElMessage.success('工具上传并校验成功，当前为禁用状态')
            addDialogVisible.value = false
            currentPage.value = 1
            await loadAgentTools()
        } else {
            addErrorMessage.value = result?.message || '工具上传或校验失败'
        }
    } finally {
        uploading.value = false
    }
}
const handleAddBeforeClose = (done) => {
    if(uploading.value) {
        ElMessage.warning('工具正在上传和校验，请稍候')
        return
    }
    done()
}
const resetAddForm = () => {
    addForm.tools_name = ''
    addForm.display_name = ''
    addForm.description = ''
    addForm.platform = 'all'
    uploadFile.value = null
    addErrorMessage.value = ''
    uploadRef.value?.clearFiles()
    addFormRef.value?.clearValidate()
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

.el-dialog.config_agent_add_dialog {
    width: 620px;
    border-radius: 5px;
}

.el-dialog.config_agent_add_dialog .el-dialog__body {
    max-height: 70vh;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(96, 103, 112, 0.28) transparent;
}

.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-track,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-corner {
    background: transparent;
}

.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-thumb {
    min-height: 32px;
    border-radius: 999px;
    background-color: rgba(96, 103, 112, 0.28);
}

.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-thumb:hover {
    background-color: rgba(96, 103, 112, 0.45);
}

.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button:single-button,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button:vertical:start:decrement,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button:vertical:end:increment,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button:horizontal:start:decrement,
.el-dialog.config_agent_add_dialog .el-dialog__body::-webkit-scrollbar-button:horizontal:end:increment {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    border: 0 !important;
    background: transparent !important;
    background-image: none !important;
    -webkit-appearance: none;
}

.agent_tool_actions {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.agent_tool_actions .el-button + .el-button {
    margin-left: 0;
}

.agent_tool_platform,
.agent_tool_upload {
    width: 100%;
}

.agent_tool_upload_tip {
    color: var(--el-text-color-secondary);
    line-height: 1.5;
}

.agent_tool_error {
    margin-top: 0.75rem;
    padding: 0.65rem 0.75rem;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    background-color: transparent;
    color: var(--el-color-danger);
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    overflow-wrap: anywhere;
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
