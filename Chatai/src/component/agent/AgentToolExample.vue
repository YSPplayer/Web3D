<template>
  <div class="agent_tool_example" v-loading="loading">
    <el-collapse v-model="openedPanels">
      <el-collapse-item name="python-example">
        <template #title>
          <div class="agent_tool_example_header">
            <span>示例</span>
            <div v-if="example" class="agent_tool_example_actions">
              <el-button link type="primary" @click.stop="copySource">
                复制代码
              </el-button>
            </div>
          </div>
        </template>

        <pre v-if="example" class="agent_tool_example_code"><code>{{ example.source }}</code></pre>
        <div v-else-if="!loading" class="agent_tool_example_empty">
          暂时无法读取工具示例
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { AgentToolExample } from '@/api/api'

const props = defineProps<{
  example: AgentToolExample | null
  loading: boolean
}>()

const openedPanels = ref<string[]>([])

const copySource = async () => {
  if (!props.example?.source) return
  try {
    await navigator.clipboard.writeText(props.example.source)
    ElMessage.success('示例代码已复制')
  } catch {
    ElMessage.error('示例代码复制失败')
  }
}

</script>

<style scoped>
.agent_tool_example {
  min-height: 48px;
  margin-top: 0.75rem;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
}

.agent_tool_example :deep(.el-collapse) {
  border: 0;
}

.agent_tool_example :deep(.el-collapse-item__header) {
  height: 42px;
  padding: 0 0.75rem;
  border-bottom: 0;
  font-size: 14px;
  font-weight: 400;
}

.agent_tool_example :deep(.el-collapse-item__wrap) {
  border-bottom: 0;
}

.agent_tool_example :deep(.el-collapse-item__content) {
  padding: 0 0.75rem 0.75rem;
}

.agent_tool_example_header {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  padding-right: 0.5rem;
}

.agent_tool_example_actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.agent_tool_example_actions .el-button + .el-button {
  margin-left: 0;
}

.agent_tool_example_code {
  max-height: 260px;
  margin: 0;
  padding: 0.75rem;
  overflow: auto;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  /* background-color: var(--el-fill-color-light); */
  color: var(--el-text-color-primary);
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre;
  scrollbar-width: thin;
  scrollbar-color: rgba(96, 103, 112, 0.28) transparent;
}

.agent_tool_example_code::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.agent_tool_example_code::-webkit-scrollbar-track,
.agent_tool_example_code::-webkit-scrollbar-corner {
  background: transparent;
}

.agent_tool_example_code::-webkit-scrollbar-thumb {
  min-width: 32px;
  min-height: 32px;
  border-radius: 999px;
  background-color: rgba(96, 103, 112, 0.28);
}

.agent_tool_example_code::-webkit-scrollbar-thumb:hover {
  background-color: rgba(96, 103, 112, 0.45);
}

.agent_tool_example_code::-webkit-scrollbar-button,
.agent_tool_example_code::-webkit-scrollbar-button:single-button,
.agent_tool_example_code::-webkit-scrollbar-button:vertical:start:decrement,
.agent_tool_example_code::-webkit-scrollbar-button:vertical:end:increment,
.agent_tool_example_code::-webkit-scrollbar-button:horizontal:start:decrement,
.agent_tool_example_code::-webkit-scrollbar-button:horizontal:end:increment {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  border: 0 !important;
  background: transparent !important;
  background-image: none !important;
  -webkit-appearance: none;
}

.agent_tool_example_empty {
  padding: 0.75rem 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  text-align: center;
}
</style>
