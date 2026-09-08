<template>
  <el-dialog
    :model-value="visible"
    :title="dialogTitle"
    width="520px"
    align-center
    class="agent_tool_approval_dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    :before-close="handleBeforeClose"
  >
    <div v-if="approval" class="agent_tool_approval">
      <div class="agent_tool_warning">
        Agent 即将执行{{ riskLabel }}操作，请确认以下工具和参数是否符合预期。
      </div>

      <div class="agent_tool_approval_rows">
        <div class="agent_tool_approval_row">
          <span class="agent_tool_approval_label">风险等级</span>
          <el-tag :type="riskTagType" effect="light">{{ riskLabel }}</el-tag>
        </div>
        <div class="agent_tool_approval_row">
          <span class="agent_tool_approval_label">显示名称</span>
          <span class="agent_tool_approval_value">
            {{ approval.tool.display_name }}
          </span>
        </div>
        <div class="agent_tool_approval_row">
          <span class="agent_tool_approval_label">工具名称</span>
          <code class="agent_tool_name">{{ approval.tool.tools_name }}</code>
        </div>
        <div class="agent_tool_approval_row is-description">
          <span class="agent_tool_approval_label">操作描述</span>
          <span class="agent_tool_approval_value">
            {{ approval.tool.description }}
          </span>
        </div>
      </div>

      <div class="agent_tool_arguments_title">调用参数</div>
      <pre class="agent_tool_arguments">{{ formattedArguments }}</pre>

      <div v-if="errorMessage" class="agent_tool_approval_error">
        {{ errorMessage }}
      </div>
    </div>

    <template #footer>
      <el-button :disabled="submitting" @click="emit('cancel')">
        取消
      </el-button>
      <el-button type="danger" :loading="submitting" @click="emit('approve')">
        确认执行
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  approval: {
    type: Object,
    default: null,
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['approve', 'cancel'])

const formattedArguments = computed(() => JSON.stringify(
  props.approval?.arguments || {},
  null,
  2,
))

const riskLabel = computed(() => {
  const labels = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  }
  return labels[props.approval?.tool?.risk_level] || '风险'
})

const riskTagType = computed(() => {
  const types = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return types[props.approval?.tool?.risk_level] || 'info'
})

const dialogTitle = computed(() => (
  props.approval?.tool?.risk_level === 'high'
    ? '高风险工具确认'
    : '工具执行确认'
))

const handleBeforeClose = () => {
  if (!props.submitting) emit('cancel')
}
</script>

<style scoped>
.agent_tool_approval {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.agent_tool_warning {
  padding: 11px 13px;
  color: #5f4b32;
  font-size: 14px;
  line-height: 1.6;
  background: #fff8eb;
  border: 1px solid #f4d7a4;
  border-radius: 7px;
}

.agent_tool_approval_rows {
  border: 1px solid #ebeef5;
  border-radius: 7px;
  overflow: hidden;
}

.agent_tool_approval_row {
  min-height: 42px;
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 0 13px;
  border-bottom: 1px solid #f0f2f5;
}

.agent_tool_approval_row:last-child {
  border-bottom: 0;
}

.agent_tool_approval_row.is-description {
  align-items: start;
  padding-top: 10px;
  padding-bottom: 10px;
}

.agent_tool_approval_label,
.agent_tool_arguments_title {
  color: #909399;
  font-size: 13px;
}

.agent_tool_approval_value {
  min-width: 0;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.agent_tool_name {
  width: fit-content;
  max-width: 100%;
  padding: 3px 7px;
  color: #606266;
  background: #f5f7fa;
  border-radius: 4px;
  overflow-wrap: anywhere;
}

.agent_tool_arguments_title {
  margin-bottom: -8px;
}

.agent_tool_arguments {
  max-height: 210px;
  margin: 0;
  padding: 12px 14px;
  overflow: auto;
  color: #303133;
  font: 13px/1.6 Consolas, Monaco, monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #f7f8fa;
  border: 1px solid #ebeef5;
  border-radius: 7px;
  scrollbar-width: thin;
  scrollbar-color: rgba(144, 147, 153, 0.45) transparent;
}

.agent_tool_arguments::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.agent_tool_arguments::-webkit-scrollbar-track {
  background: transparent;
}

.agent_tool_arguments::-webkit-scrollbar-thumb {
  background: rgba(144, 147, 153, 0.4);
  border-radius: 6px;
}

.agent_tool_arguments::-webkit-scrollbar-button {
  display: none;
  width: 0;
  height: 0;
}

.agent_tool_approval_error {
  padding: 9px 12px;
  color: #f56c6c;
  font-size: 13px;
  line-height: 1.5;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}
</style>
