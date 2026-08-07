<template>
   <el-dialog @opened="handleOpen"  @closed="handleClosed" v-model="dialogVisible" title="系统设置" class="config_dialog" align-center :close-on-click-modal="false">
    <div class="flex_colum_center">
        <el-tabs v-model="activeName" class="config_tab" tab-position='left'>
            <el-tab-pane name="model">
                 <template #label>
                        <span class="config_tab_label">模型管理</span>
                </template>
                <div class="config_model flex_colum">
                    <el-switch
                    v-model="onlineModel"
                    :disabled = "!onlineModel && localModelState !== 'stopped' "
                    :active-text="onlineModel ? '在线模型' : '本地模型'"   @change="handleModelModeChange">
                </el-switch>
                    <div  v-if="onlineModel" class="flex_row">
                        <span class="center_span tab_span">密钥</span>
                        <el-input class = "model_apikey" v-model="configForm.apikey"></el-input>
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
                        <span class="center_span tab_span">模型</span>
                        <el-cascader
                            class = "model_select"
                            v-model="modelSelectValue"
                            :disabled = "!onlineModel && localModelState !== 'stopped' "
                            :options="filteredModelOptions"
                            :props="{ expandTrigger: 'hover' }"
                            @change='modelSelectChange'
                            >
                            <template #default="{ data }">
                                <div class="model_option ">
                                    <img
                                        v-if="data.icon"
                                        :src="data.icon"
                                        class="model_option_icon"
                                        alt=""
                                    />
                                    <span class="model_option_label">
                                        {{ data.label }}
                                    </span>
                                </div>
                            </template>
                        </el-cascader>
                        <img v-if="modelImageUrl != ''" class="model_logo_img" :src="modelImageUrl">
                    </div>
                    <div v-if="onlineModel" class="flex_row">
                        <span class="center_span tab_span">VPN</span>
                        <el-switch style="margin-left: 1rem;"
                        v-model="proxyActive"
                        active-text="启用代理">
                        </el-switch>
                    </div>
                    <div v-if="onlineModel" class="flex_row">
                        <span class="center_span tab_span" style="margin-left: 3rem;">IP</span>
                            <el-input class = "model_apiip" v-model="configForm.agentip" @input="formatIpInput"></el-input>
                            <span class="center_span tab_span" style="margin-left: 1rem;">端口</span>
                            <el-input class = "model_apiport" v-model="configForm.agentport" @input="formatPortInput"></el-input>
                    </div>
                    <span class="center_span span_count">资源管理统计</span>
                    <div v-if="!onlineModel" class="flex_row system_status">
                            <span class="center_span">CPU内存占用率</span>
                            <el-progress class="system_status_progress" :percentage="configForm.cpuMemoryPercent"></el-progress>
                    </div>
                    <div v-if="!onlineModel" class="flex_row system_status">
                            <span class="center_span">CPU使用率</span>
                            <el-progress class="system_status_progress" :percentage="configForm.cpuPercent"></el-progress>
                    </div>
                      <div v-if="!onlineModel" class="flex_row system_status">
                            <span class="center_span">GPU内存占用率</span>
                            <el-progress class="system_status_progress" :percentage="configForm.gpuMemoryPercent"></el-progress>
                    </div>
                    <div v-if="!onlineModel" class="flex_row system_status">
                            <span class="center_span">GPU使用率</span>
                            <el-progress class="system_status_progress" :percentage="configForm.gpuPercent"></el-progress>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <tokenchart  :tokenData ="configForm.tokenData" :tokenCount="configForm.tokenCount"
                        :tokenDate = "configForm.tokenDate" 
                        @updateUserTokens="updateUserTokens"/>
                    </div>
                </div>
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
    import { ref,reactive,computed, watch } from 'vue'
    import { ChatAiApi } from '@/api/api'
    import { user } from '@/store/store'
    import { ElMessage } from 'element-plus'
    import { Util } from '@/shared/util.ts'
    import { Loading } from '@element-plus/icons-vue'
    import modelStart from '@/assets/modelStart.svg'
    import modelStop from '@/assets/modelStop.svg'
    import modelStarting from '@/assets/modelStarting.svg'
    import tokenchart from './tokenchart.vue'
    const modelSelectValue = ref([])
    const configForm = reactive({
        apikey: '',
        agentip:'',
        agentport:'',
        tokenData:[],
        tokenCount:0,
        tokenDate:'',
        cpuMemoryPercent:0,
        cpuPercent:0,
        gpuPercent:0,
        gpuMemoryPercent:0,
    })
    //stopped / starting / ready / error
    const localModelState = ref('')
    const activeName = ref('model')
    const modelImageUrl = ref('')
    const onlineModel = ref(true)
    const proxyActive = ref(false)
    const modelOptions = ref([])
    const dialogVisible = ref(false)
    const saveconfigLoading = ref(false)
    const systemMetrics = ref(null)
    let timer = null
    const modelSelectChange = async (syncOnlineModel = true)=> {
        if (modelSelectValue.value.length !== 2) return
        const config = await ChatAiApi.getModelConfigStateApi(user.userid,
            modelSelectValue.value[0],modelSelectValue.value[1]
        )
        if(config.code == 200) {
            const data = config.data
            if(Util.isEmptyObject(data)) {
                 if (syncOnlineModel) {
                    onlineModel.value = modelSelectValue.value[0] !== 'local'
                 }
                 configForm.apikey = ''
                 modelImageUrl.value = ''
                 return
            }
            if (syncOnlineModel) {
                onlineModel.value =  data.isonline === 1
            }
            configForm.apikey =  data.apikey ? Util.base64ToString(data.apikey) : ''
            modelImageUrl.value = data.logo || ''
        } 
    }
    const filteredModelOptions = computed(() => {
    if (onlineModel.value) {
        // 在线模型：排除 local
        return modelOptions.value.filter(item => item.value !== 'local')
    }
        // 本地模型：只保留 local
        return modelOptions.value.filter(item => item.value === 'local')
    })
    const handleClosed = async ()=>{
         if (timer) {
            clearInterval(timer)
        }
    }

    const updateSystemMetrics = async () => {
        const result = await ChatAiApi.getSystemMetricsApi()
        if (result?.code === 200) {
            const data = result.data
            const gpu = Array.isArray(data.gpu) && data.gpu.length > 0
            ? data.gpu[0]
            : null
            configForm.cpuPercent =data.cpu.percent
            configForm.cpuMemoryPercent = data.memory.percent
            if(gpu) {
                configForm.gpuPercent = gpu.gpu_percent
                configForm.gpuMemoryPercent = gpu.memory_percent
            }
           
        }
    }

    const handleRunModel = async ()=>{
        await updatelocalModelState()
        //stopped / starting / ready / error
        if( user.localmodelstate === 'starting') return;
        if(user.localmodelstate ==='ready') {
           const result =  await ChatAiApi.stopLocalModelApi()
           if(result?.code != 200) {
                ElMessage.error('本地模型停止失败')
           } else {
                ElMessage.success('本地模型已停止')
           }
        } else {
            localModelState.value = 'starting'
            const result = await ChatAiApi.startLocalModelApi(user.userid, user.modelconfigid)
            if(result?.code != 200)  {
                    ElMessage.error('本地模型运行失败')
            } else {
                    ElMessage.success('本地模型运行成功')
            }
        }
        await updatelocalModelState()
    }
    const runModelIcon = computed(() =>{
        if(localModelState.value === 'stopped') return modelStart
        if(localModelState.value === 'ready') return modelStop
        if(localModelState.value === 'error') return modelStart
        if(localModelState.value === 'starting') return modelStarting
        return ''
    })

    watch(() => user.localmodelstate,(newState) => {
        localModelState.value = newState
    },{ immediate: true })

    const updatelocalModelState = async ()=>{
         const result = await ChatAiApi.getLocalModelStatusApi()
         if(result?.code == 200) {
             const data = result.data
             user.localmodelstate = data.status
              localModelState.value = user.localmodelstate
         }
    }
    const handleModelModeChange = async () => {
        await updateUserModelConfig(onlineModel.value)
       
    }
    const handleOpen = async ()=> {
        updateSystemMetrics()
        timer = window.setInterval(updateSystemMetrics, 1000)
        await updateUserModelConfig()
        await updatelocalModelState()
        user.modelname = modelSelectValue?.value.length > 1 
        ?  modelSelectValue.value[1] : ""
    } 
    const updateUserTokens = async(date) => {
        const result = await ChatAiApi.getTokensCountByUserIdApi(user.userid,date)
        if(result?.code == 200) {
            const data = result.data
            configForm.tokenData = data.items
            configForm.tokenCount = data.total_tokens
            configForm.tokenDate = data.date
        }
    }
    const updateUserModelConfig = async (targetOnlineModel = null)=> {
      //获取到所有模型
      modelOptions.value = []
      const modelDatas = await ChatAiApi.modelsApi()
      if(modelDatas.code == 200) {
        const data = modelDatas.data
        if(!data) return
        user.models = data //设置当前的所有模型
        data.forEach(item => {
            const modelType = item.model_type
            const modelName = item.model_name
            let target = modelOptions.value.find(item => item.value === modelType)
            if (!target) {    
                const newitem = {
                    value: modelType,
                    label: modelType,
                    icon:item.logo_path,
                    children: []
                }
                modelOptions.value.push(newitem)
                target = newitem
            }
            target.children.push({
                value:modelName,
                label:modelName
            })
        });
      }
      await updateUserTokens(Util.getToday())
      //设置当前的激活模型
      const userconfig = await ChatAiApi.getUserModelConfigApi(user.userid)
      if(userconfig.code == 200) {
            const data = userconfig.data
            const hasConfig = !Util.isEmptyObject(data)
            const shouldUseCurrentConfig = targetOnlineModel === null || (hasConfig && (data.isonline === 1) === targetOnlineModel)

            if(shouldUseCurrentConfig && hasConfig) {
                onlineModel.value = data.isonline === 1
                configForm.apikey = data.apikey ? Util.base64ToString(data.apikey) : ''
                modelSelectValue.value = [data.modeltype,data.modelname]
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

            if(!onlineModel.value) {
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
    }
    const formatIpInput = (value) => {
        configForm.agentip = value.replace(/[^0-9.:]/g, '')
    }
    const formatPortInput = (value) => {
        configForm.agentport = value.replace(/[^0-9.:]/g, '')
    }
    const saveConfig = async () => {
        saveconfigLoading.value = true
        if(activeName.value === 'model') {
            const config = {
                userid:user.userid,
                modeltype:modelSelectValue.value[0],
                modelname:modelSelectValue.value[1],
                apikey:Util.stringToBase64(configForm.apikey),
                proxyhost:configForm.agentip,
                proxyport:Number(configForm.agentport),
                proxyactive:proxyActive.value ? 1 : 0
            } 
            const result = await ChatAiApi.saveModelConfigApi(config)
            if(result?.code == 200) {
                ElMessage.success('配置保存成功！')
                const data = result.data
                user.modelconfigid = data.modelconfigid
                user.modelid = data.modelid
                user.modelname = data.modelname
            }
        }
        saveconfigLoading.value = false
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
    updateUserModelConfig
    })
</script>
<style>
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
.config_tab .model_apikey {
    width: 500px;
    margin-left: 1rem;
}
.config_tab .model_apiip {
    width: 300px;
    margin-left: 0.5rem;
}
.config_tab .model_apiport {
    width: 100px;
    margin-left: 0.5rem;
}
.config_tab .model_select {
    width: 200px;
    margin-left: 1rem;
}
.config_bottom {
    width: 100%;
}

.config_bottom .el-button {
    width: 100px;
    height: 35px;
    margin-left: auto;
    font-size: 16.5px;
}
.config_tab .tab_span {
     font-size: 0.95rem;
}
.config_tab .tab_child_span {
     font-size: 0.75rem;
}
.config_model {
    width: 100%;
    gap:1rem;
}
.span_count {
     font-size: 16px;
     font-weight: 600
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
.model_option .model_option_icon {
    width: 22px;
    height: 22px;
    flex: 0 0 22px;
    object-fit: contain;
    display: block;
}
.model-cascader-model_option .model_option_label {
    white-space: nowrap;
    font-size: 15px;
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
