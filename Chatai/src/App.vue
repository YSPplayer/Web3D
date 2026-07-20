<template>
    <div class ='container flex_row'>
        <leftmenu ref="leftmenuRef" @showConfigDialog= 'showConfigDialog'  />
        <chatcontainer/>
    </div>
    <login ref="loginRef" @updateUserModelConfig = 'updateUserModelConfig'/>
    <config ref="configRef"/>
</template>
<script setup>
import leftmenu from '@/component/leftmenu.vue';
import chatcontainer from '@/component/chatcontainer.vue';
import login from '@/component/login.vue'
import config from '@/component/config.vue'
import { ref, onMounted } from 'vue'
import { ChatAiApi } from '@/api/api.ts';
import { user } from '@/store/store.ts';
const loginRef = ref(null)
const configRef = ref(null)
const leftmenuRef = ref(null)
const showConfigDialog = ()=>{
   configRef.value?.openDialog()
}
onMounted(()=>{
   loginRef.value?.openDialog()
})
const updateUserModelConfig = async ()=> {
    await configRef.value?.updateUserModelConfig() 
    //获取到用户的最新的会话记录
    const result = await ChatAiApi.getConversationApi(user.userid,
        user.modelconfigid
    )
    if(result.code == 200) {
        const data = result.data
        if(!data) return 
        await leftmenuRef.value?.updateChatList(data)
    }
}
</script>
<style scoped>
.leftmenu {
    width: 15%;
    height: 100%;
    background-color: #FFFFFF;
    border-right: 1px solid #ccc;
}
.chatcontainer {
    width: 85%;
    height: 100%;
    background-color: #FFFFFF;
}
.container {
    background-color: #FFFFFF;
    /*vw,相对于浏览器窗口的变化尺寸*/
    width: 100vw; 
    height: 100vh;
}    
</style>