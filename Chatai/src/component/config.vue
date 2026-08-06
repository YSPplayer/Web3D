<template>
   <el-dialog @opened="handleOpen" v-model="dialogVisible" title="系统设置" class="config_dialog" align-center :close-on-click-modal="false">
    <div class="flex_colum_center">
        <el-tabs v-model="activeName" class="config_tab" tab-position='left'>
            <el-tab-pane name="model">
                 <template #label>
                        <span class="config_tab_label">模型管理</span>
                </template>
                <div class="config_model flex_colum">
                    <el-switch
                    v-model="onlineModel"
                    :active-text="onlineModel ? '在线模型' : '本地模型'">
                    </el-switch>
                    <div  v-if="onlineModel" class="flex_row">
                        <span class="center_span tab_span">密钥</span>
                        <el-input class = "model_apikey" v-model="configForm.apikey"></el-input>
                    </div>
                    <div v-if="onlineModel" class="flex_row">
                        <span class="center_span tab_span">模型</span>
                        <el-cascader
                            class = "model_select"
                            v-model="modelSelectValue"
                            :options="modelOptions"
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
        tokenDate:''
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
    const modelSelectChange = async ()=> {
        const config = await ChatAiApi.getModelConfigStateApi(user.userid,
            modelSelectValue.value[0],modelSelectValue.value[1]
        )
        if(config.code == 200) {
            const data = config.data
            if(Util.isEmptyObject(data)) {
                 onlineModel.value = false
                 configForm.apikey = ''
                 modelImageUrl.value = ''
            }
            onlineModel.value = data.isonline
            configForm.apikey = Util.base64ToString(data.apikey)
            modelImageUrl.value = data.logo
        } 
    }
    const handleRunModel = async ()=>{
        await ChatAiApi.startLocalModelApi()
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
        }
    )
    const updatelocalModelState = async ()=>{
         const result = await ChatAiApi.getLocalModelStatusApi()
         if(result?.code == 200) {
             const data = result.data
             user.localmodelstate = data.status
         }
    }
    const handleOpen = async ()=> {
      await updateUserModelConfig()
      await updatelocalModelState()
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
    const updateUserModelConfig = async ()=> {
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
            if(Util.isEmptyObject(data)) {
                onlineModel.value = false
                configForm.apikey = ''
                configForm.agentip = ''
                configForm.agentport = ''
                proxyActive.value = false
                modelSelectValue.value = []
                modelImageUrl.value = ''
                user.modelconfigid = -1
                user.modeltype = ''
                user.modellogo = ''
                user.modelid = -1
            } else {
                onlineModel.value = data.isonline === 1
                configForm.apikey = Util.base64ToString(data.apikey)
                modelSelectValue.value = [data.modeltype,data.modelname]
                modelImageUrl.value = data.logo  
                user.modelconfigid = data.modelconfigid
                user.modeltype = data.modeltype
                user.modellogo = data.logo
                user.modelid = data.modelid
                configForm.agentip = data.proxyhost
                configForm.agentport = String(data.proxyport)
                proxyActive.value = data.proxyactive === 1
            }
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
                isonline:onlineModel.value ? 1 : 0,
                proxyhost:configForm.agentip,
                proxyport:Number(configForm.agentport),
                proxyactive:proxyActive.value ? 1 : 0
            } 
            const result = await ChatAiApi.saveModelConfigApi(config)
            if(result?.code == 200) {
                ElMessage.success('配置保存成功！')
                const data = result.data
                user.modelid = data.modelid
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