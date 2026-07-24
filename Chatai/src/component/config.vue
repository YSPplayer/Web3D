<template>
   <el-dialog @open="handleOpen" v-model="dialogVisible" title="系统设置" class="config_dialog" align-center :close-on-click-modal="false">
    <div class="flex_colum_center">
        <el-tabs v-model="activeName" class="config_tab" tab-position='left' style="height: 200px;">
            <el-tab-pane name="model">
                 <template #label>
                        <span class="config_tab_label">模型管理</span>
                </template>
                <div class="config_model flex_colum">
                    <el-switch
                    v-model="onlineModel"
                    active-text="在线模型">
                    </el-switch>
                    <div class="flex_row">
                        <span class="center_span tab_span">密钥</span>
                        <el-input class = "model_apikey" v-model="configForm.apikey"></el-input>
                    </div>
                    <div class="flex_row">
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
    import { ref,reactive,computed } from 'vue'
    import { ChatAiApi } from '@/api/api'
    import { user } from '@/store/store'
    import { ElMessage } from 'element-plus'
    import { Util } from '@/shared/util.ts'
    const modelSelectValue = ref([])
    const configForm = reactive({
        apikey: '',
    })
    const activeName = ref('model')
    const modelImageUrl = ref('')
    const onlineModel = ref(true)
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
    const handleOpen = async ()=> {
      await updateUserModelConfig()
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
      //设置当前的激活模型
      const userconfig = await ChatAiApi.getUserModelConfigApi(user.userid)
      if(userconfig.code == 200) {
            const data = userconfig.data
            if(Util.isEmptyObject(data)) {
                onlineModel.value = false
                configForm.apikey = ''
                modelSelectValue.value = []
                modelImageUrl.value = ''
                user.modelconfigid = -1
                user.modeltype = ''
                user.modellogo = ''
                user.modelid = -1
            } else {
                onlineModel.value = data.isonline
                configForm.apikey = Util.base64ToString(data.apikey)
                modelSelectValue.value = [data.modeltype,data.modelname]
                modelImageUrl.value = data.logo  
                user.modelconfigid = data.modelconfigid
                user.modeltype = data.modeltype
                user.modellogo = data.logo
                user.modelid = data.modelid
            }
      }
    }
    const saveConfig = async () => {
        saveconfigLoading.value = true
        if(activeName.value === 'model') {
            const config = {
                userid:user.userid,
                modeltype:modelSelectValue.value[0],
                modelname:modelSelectValue.value[1],
                apikey:Util.stringToBase64(configForm.apikey),
                isonline:onlineModel.value ? 1 : 0
            } 
            const result = await ChatAiApi.saveModelConfigApi(config)
            if(result?.code == 200) {
                ElMessage.success('配置保存成功！')
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