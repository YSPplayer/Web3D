<template>
  <div class="config_model flex_colum">
    <el-switch
      v-model="onlineModel"
      :disabled="!onlineModel && localModelState !== 'stopped'"
      :active-text="onlineModel ? '在线模型' : '本地模型'"
      @change="handleModelModeChange"
    />
    <div v-if="onlineModel" class="flex_row">
      <span class="center_span tab_span">密钥</span>
      <el-input v-model="configForm.apikey" class="model_apikey" />
    </div>
    <div v-if="!onlineModel" class="flex_row" style="gap: 0.5rem;">
      <span class="center_span">启动模型</span>
      <div class="config_run_model" @click="handleRunModel">
        <img
          class="fill_img"
          :class="{ run_model_spinning: localModelState === 'starting' }"
          :src="runModelIcon"
          alt=""
        />
      </div>
    </div>
    <div class="flex_row">
      <span class="center_span tab_span"  style="margin-right: 1rem;">模型</span>
      <el-cascader
        v-model="modelSelectValue"
        class="model_select"
        popper-class="config-model-popper"
        :disabled="!onlineModel && localModelState !== 'stopped'"
        :options="filteredModelOptions"
        :props="{ expandTrigger: 'hover' }"
        @change="modelSelectChange"
      >
        <template #default="{ data }">
          <div class="model_option">
            <img
              v-if="data.icon"
              :src="data.icon"
              class="model_option_icon"
              alt=""
            />
            <span class="model_option_label">{{ data.label }}</span>
          </div>
        </template>
      </el-cascader>
      <img v-if="modelImageUrl !== ''" class="model_logo_img" :src="modelImageUrl">
    </div>
    <div v-if="onlineModel" class="flex_row">
      <span class="center_span tab_span">VPN</span>
      <el-switch
        v-model="proxyActive"
        style="margin-left: 1rem;"
        active-text="启用代理"
      />
    </div>
    <div v-if="onlineModel" class="flex_row">
      <span class="center_span tab_span" style="margin-left: 3rem;">IP</span>
      <el-input v-model="configForm.agentip" class="model_apiip" @input="formatIpInput" />
      <span class="center_span tab_span" style="margin-left: 1rem;">端口</span>
      <el-input v-model="configForm.agentport" class="model_apiport" @input="formatPortInput" />
    </div>
    <span class="center_span span_count">资源管理统计</span>
    <div v-if="!onlineModel" class="flex_row system_status">
      <span class="center_span">CPU内存占用率</span>
      <el-progress class="system_status_progress" :percentage="configForm.cpuMemoryPercent" :color="progressColors" />
    </div>
    <div v-if="!onlineModel" class="flex_row system_status">
      <span class="center_span">CPU使用率</span>
      <el-progress class="system_status_progress" :percentage="configForm.cpuPercent" :color="progressColors" />
    </div>
    <div v-if="!onlineModel" class="flex_row system_status">
      <span class="center_span">GPU内存占用率</span>
      <el-progress class="system_status_progress" :percentage="configForm.gpuMemoryPercent" :color="progressColors" />
    </div>
    <div v-if="!onlineModel" class="flex_row system_status">
      <span class="center_span">GPU使用率</span>
      <el-progress class="system_status_progress" :percentage="configForm.gpuPercent" :color="progressColors" />
    </div>
    <div style="margin-bottom: 1rem;">
      <TokenChart
        :token-data="configForm.tokenData"
        :token-count="configForm.tokenCount"
        :token-date="configForm.tokenDate"
        @update-user-tokens="updateUserTokens"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatAiApi } from '@/api/api'
import { user } from '@/store/store'
import { Util } from '@/shared/util'
import modelStart from '@/assets/modelStart.svg'
import modelStop from '@/assets/modelStop.svg'
import modelStarting from '@/assets/modelStarting.svg'

type LoadingChangeHandler = (loading: boolean) => void

export const useConfigModel = (onLoadingChange: LoadingChangeHandler) => {
  const modelSelectValue = ref<string[]>([])
  const configForm = reactive({
    apikey: '',
    agentip: '',
    agentport: '',
    tokenData: [],
    tokenCount: 0,
    tokenDate: '',
    cpuMemoryPercent: 0,
    cpuPercent: 0,
    gpuPercent: 0,
    gpuMemoryPercent: 0,
  })
  const progressColors = [
    { color: '#67c23a', percentage: 40 },
    { color: '#e6a23c', percentage: 70 },
    { color: '#f56c6c', percentage: 100 },
  ]
  // stopped / starting / ready / error
  const localModelState = ref('')
  const modelImageUrl = ref('')
  const onlineModel = ref(true)
  const proxyActive = ref(false)
  const modelOptions = ref<any[]>([])
  let timer: ReturnType<typeof window.setInterval> | null = null

  const filteredModelOptions = computed(() => {
    if (onlineModel.value) {
      // 在线模型：排除 local
      return modelOptions.value.filter(item => item.value !== 'local')
    }
    // 本地模型：只保留 local
    return modelOptions.value.filter(item => item.value === 'local')
  })

  const runModelIcon = computed(() => {
    if (localModelState.value === 'stopped') return modelStart
    if (localModelState.value === 'ready') return modelStop
    if (localModelState.value === 'error') return modelStart
    if (localModelState.value === 'starting') return modelStarting
    return ''
  })

  const modelSelectChange = async (syncOnlineModel = true) => {
    if (modelSelectValue.value.length !== 2) return
    const config = await ChatAiApi.getModelConfigStateApi(
      user.userid,
      modelSelectValue.value[0],
      modelSelectValue.value[1],
    )
    if (config.code !== 200) return

    const data = config.data
    if (Util.isEmptyObject(data)) {
      if (syncOnlineModel) {
        onlineModel.value = modelSelectValue.value[0] !== 'local'
      }
      configForm.apikey = ''
      modelImageUrl.value = ''
      return
    }

    if (syncOnlineModel) {
      onlineModel.value = data.isonline === 1
    }
    configForm.apikey = data.apikey ? Util.base64ToString(data.apikey) : ''
    modelImageUrl.value = data.logo || ''
  }

  const stopMetricsTimer = () => {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
  }

  const updateSystemMetrics = async () => {
    const result = await ChatAiApi.getSystemMetricsApi()
    if (result?.code !== 200) return

    const data = result.data
    const gpu = Array.isArray(data.gpu) && data.gpu.length > 0
      ? data.gpu[0]
      : null
    configForm.cpuPercent = data.cpu.percent
    configForm.cpuMemoryPercent = data.memory.percent
    if (gpu) {
      configForm.gpuPercent = gpu.gpu_percent
      configForm.gpuMemoryPercent = gpu.memory_percent
    }
  }

  const setMetricsPolling = (enabled: boolean) => {
    stopMetricsTimer()
    if (!enabled) return

    void updateSystemMetrics()
    timer = window.setInterval(updateSystemMetrics, 1000)
  }

  const updateLocalModelState = async () => {
    const result = await ChatAiApi.getLocalModelStatusApi()
    if (result?.code === 200) {
      user.localmodelstate = result.data.status
      localModelState.value = user.localmodelstate
    }
  }

  const handleRunModel = async () => {
    await updateLocalModelState()
    if (user.localmodelstate === 'starting') return

    if (user.localmodelstate === 'ready') {
      const result = await ChatAiApi.stopLocalModelApi()
      if (result?.code !== 200) {
        ElMessage.error('本地模型停止失败')
      } else {
        ElMessage.success('本地模型已停止')
      }
    } else {
      localModelState.value = 'starting'
      const result = await ChatAiApi.startLocalModelApi(user.userid, user.modelconfigid)
      if (result?.code !== 200) {
        ElMessage.error('本地模型运行失败')
      } else {
        ElMessage.success('本地模型运行成功')
      }
    }
    await updateLocalModelState()
  }

  const updateUserTokens = async (date: string) => {
    const result = await ChatAiApi.getTokensCountByUserIdApi(user.userid, date)
    if (result?.code === 200) {
      const data = result.data
      configForm.tokenData = data.items
      configForm.tokenCount = data.total_tokens
      configForm.tokenDate = data.date
    }
  }

  const updateUserModelConfig = async (targetOnlineModel: boolean | null = null) => {
    //获取到所有模型
    modelOptions.value = []
    const modelDatas = await ChatAiApi.modelsApi()
    if (modelDatas.code === 200) {
      const data = modelDatas.data
      if (!data) return
      user.models = data //设置当前的所有模型
      data.forEach((item: any) => {
        const modelType = item.model_type
        const modelName = item.model_name
        let target = modelOptions.value.find(option => option.value === modelType)
        if (!target) {
          target = {
            value: modelType,
            label: modelType,
            icon: item.logo_path,
            children: [],
          }
          modelOptions.value.push(target)
        }
        target.children.push({
          value: modelName,
          label: modelName,
        })
      })
    }

    await updateUserTokens(Util.getToday())
    //设置当前的激活模型
    const userconfig = await ChatAiApi.getUserModelConfigApi(user.userid)
    if (userconfig.code !== 200) return

    const data = userconfig.data
    const hasConfig = !Util.isEmptyObject(data)
    const shouldUseCurrentConfig = targetOnlineModel === null
      || (hasConfig && (data.isonline === 1) === targetOnlineModel)

    if (shouldUseCurrentConfig && hasConfig) {
      onlineModel.value = data.isonline === 1
      configForm.apikey = data.apikey ? Util.base64ToString(data.apikey) : ''
      modelSelectValue.value = [data.modeltype, data.modelname]
      modelImageUrl.value = data.logo
      user.modelconfigid = data.modelconfigid
      user.modeltype = data.modeltype
      user.modellogo = data.logo
      user.modelid = data.modelid
      configForm.agentip = data.proxyhost
      configForm.agentport = String(data.proxyport)
      proxyActive.value = data.proxyactive === 1
      return
    }

    onlineModel.value = targetOnlineModel ?? false
    configForm.apikey = ''
    modelImageUrl.value = ''
    user.modelconfigid = -1
    user.modeltype = ''
    user.modellogo = ''
    user.modelid = -1

    if (!onlineModel.value) {
      configForm.agentip = ''
      configForm.agentport = ''
      proxyActive.value = false
    }

    const group = filteredModelOptions.value[0]
    const model = group?.children?.[0]
    if (!group || !model) {
      modelSelectValue.value = []
      return
    }

    modelSelectValue.value = [group.value, model.value]
    await modelSelectChange(false)
  }

  const handleModelModeChange = async () => {
    await updateUserModelConfig(onlineModel.value)
  }

  const formatIpInput = (value: string) => {
    configForm.agentip = value.replace(/[^0-9.:]/g, '')
  }

  const formatPortInput = (value: string) => {
    configForm.agentport = value.replace(/[^0-9.:]/g, '')
  }

  const saveConfig = async (showMessage = true) => {
    onLoadingChange(true)
    try {
      const config = {
        userid: user.userid,
        modeltype: modelSelectValue.value[0],
        modelname: modelSelectValue.value[1],
        apikey: Util.stringToBase64(configForm.apikey),
        proxyhost: configForm.agentip,
        proxyport: Number(configForm.agentport),
        proxyactive: proxyActive.value ? 1 : 0,
      }
      const result = await ChatAiApi.saveModelConfigApi(config)
      if (result?.code === 200) {
        if (showMessage) ElMessage.success('配置保存成功！')
        const data = result.data
        user.modelconfigid = data.modelconfigid
        user.modelid = data.modelid
        user.modelname = data.modelname
      }
      return result
    } finally {
      onLoadingChange(false)
    }
  }

  const initialize = async () => {
    await updateUserModelConfig()
    await updateLocalModelState()
    user.modelname = modelSelectValue.value.length > 1
      ? modelSelectValue.value[1]
      : ''
    await saveConfig(false)
  }

  const dispose = () => {
    stopMetricsTimer()
  }

  watch(
    () => user.localmodelstate,
    newState => {
      localModelState.value = newState
    },
    { immediate: true },
  )

  onUnmounted(stopMetricsTimer)

  return {
    modelSelectValue,
    configForm,
    progressColors,
    localModelState,
    modelImageUrl,
    onlineModel,
    proxyActive,
    filteredModelOptions,
    runModelIcon,
    modelSelectChange,
    handleRunModel,
    handleModelModeChange,
    formatIpInput,
    formatPortInput,
    updateUserTokens,
    updateUserModelConfig,
    setMetricsPolling,
    initialize,
    dispose,
    saveConfig,
  }
}
</script>

<script setup lang="ts">
import TokenChart from './tokenchart.vue'

const props = defineProps({
  manager: {
    type: Object,
    required: true,
  },
})

const {
  modelSelectValue,
  configForm,
  progressColors,
  localModelState,
  modelImageUrl,
  onlineModel,
  proxyActive,
  filteredModelOptions,
  runModelIcon,
  modelSelectChange,
  handleRunModel,
  handleModelModeChange,
  formatIpInput,
  formatPortInput,
  updateUserTokens,
} = props.manager
</script>

<style scoped>
.config_model {
  width: 100%;
  gap: 1rem;
}

.run_model_spinning {
  animation: run-model-spin 2s linear infinite;
}

@keyframes run-model-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.config_run_model {
  width: 36px;
  height: 36px;
}

.config_run_model:hover {
  cursor: pointer;
}

.model_logo_img {
  height: 30px;
  aspect-ratio: 1 / 1;
  object-fit: fill;
  margin-left: 1rem;
}

.model_apikey {
  width: 500px;
  margin-left: 1rem;
}

.model_apiip {
  width: 300px;
  margin-left: 0.5rem;
}

.model_apiport {
  width: 100px;
  margin-left: 0.5rem;
}

.model_select {
  width: 200px;
  margin-left: 1rem;
}

.tab_span {
  font-size: 0.95rem;
}

.span_count {
  font-size: 16px;
  font-weight: 600;
}

.system_status_progress {
  width: 200px;
  margin-left: auto;
  margin-right: 20rem;
}

.model_option {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.model_option_icon {
  width: 22px;
  height: 22px;
  flex: 0 0 22px;
  object-fit: contain;
  display: block;
}

.model_option_label {
  white-space: nowrap;
  font-size: 15px;
}
</style>
