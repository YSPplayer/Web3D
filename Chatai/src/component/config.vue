<template>
   <el-dialog @open="handleOpen" v-model="dialogVisible" title="系统设置" class="config_dialog" align-center :close-on-click-modal="false">
       <el-tabs class="config_tab" tab-position='left' style="height: 200px;">
            <el-tab-pane>
                 <template #label>
                        <span class="config_tab_label">模型管理</span>
                </template>
                <div class="config_model flex_colum">
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
                            ></el-cascader>
                    </div>
                </div>
            </el-tab-pane>
        </el-tabs>
    </el-dialog>

</template>
<script setup>
    import { ref,reactive,computed } from 'vue'
    import { ChatAiApi } from '@/api/api'
    const modelSelectValue = ref([])
    const configForm = reactive({
        apikey: '',
    })
    const modelOptions = ref([])
    const dialogVisible = ref(false)
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
.config_tab .tab_span {
     font-size: 0.95rem;
}
.config_model {
    width: 100%;
    gap:1rem;
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