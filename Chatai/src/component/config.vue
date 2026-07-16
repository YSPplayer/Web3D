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
    const modelSelectValue = ref([])
    const configForm = reactive({
        apikey: '',
    })
    const activeName = ref('model')
    const onlineModel = ref(true)
    const modelOptions = ref([])
    const dialogVisible = ref(false)
    const saveconfigLoading = ref(false)
    const handleOpen = async ()=> {
      modelOptions.value = []
      const modelDatas = await ChatAiApi.modelsApi()
      if(modelDatas.code == 200) {
        modelDatas?.data.forEach(item => {
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

    } 
    const saveConfig = async () => {
        saveconfigLoading.value = true
        if(activeName.value === 'model') {
            const config = {
                userid:user.userid,
                modeltype:modelSelectValue.value[0],
                modelname:modelSelectValue.value[1],
                apikey:configForm.apikey,
                isonline:onlineModel.value ? 1 : 0,
                isactive:1
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
    closeDialog
    })
</script>
<style>
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