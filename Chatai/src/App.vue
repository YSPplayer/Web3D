<template>
    <div v-if="authStatus === 'checking'" class="auth_bootstrap" v-loading="true"></div>
    <div v-else-if="authStatus === 'authenticated'" class ='container flex_row'>
        <leftmenu ref="leftmenuRef" @showConfigDialog= 'showConfigDialog' @updateChatMessage = 'updateChatMessage' @requestLogout="handleLogout" />
        <chatcontainer ref="chatcontainerRef" @updateTitleMessage ='updateTitleMessage'/>
    </div>
    <login ref="loginRef" @updateUserModelConfig = 'updateUserModelConfig'/>
    <config v-if="authStatus === 'authenticated'" ref="configRef"/>
</template>
<script setup>
import leftmenu from '@/component/leftmenu.vue';
import chatcontainer from '@/component/chatcontainer.vue';
import login from '@/component/login.vue'
import config from '@/component/config.vue'
import { ref, onMounted, nextTick } from 'vue'
import { ChatAiApi } from '@/api/api.ts';
import { applyAuthenticatedUser, resetUser, user } from '@/store/store.ts';
import { request } from '@/api/request.ts';
import { ElMessage, ElMessageBox } from 'element-plus';
const loginRef = ref(null)
const configRef = ref(null)
const leftmenuRef = ref(null)
const chatcontainerRef = ref(null)
const authStatus = ref('checking')
const logoutLoading = ref(false)
const showConfigDialog = ()=>{
   configRef.value?.openDialog()
}
const openLoginAfterRender = () => {
   nextTick(() => loginRef.value?.openDialog())
}
const handleAuthFailure = () => {
   request.clearAccessToken()
   resetUser()
   authStatus.value = 'anonymous'
   openLoginAfterRender()
}
const handleLogout = async () => {
   if(logoutLoading.value) return
   try {
      await ElMessageBox.confirm(
         '退出后需要重新登录，是否确认退出？',
         '退出登录',
         {
            confirmButtonText: '退出',
            cancelButtonText: '取消',
            type: 'warning',
            closeOnClickModal: false,
            closeOnPressEscape: true
         }
      )
   } catch {
      return
   }

   logoutLoading.value = true
   try {
      try {
         await chatcontainerRef.value?.stopChatMessage?.()
      } catch {
         // 停止生成失败时仍需继续退出登录
      }
      const result = await ChatAiApi.logoutApi()
      if(result?.code === 200) {
         ElMessage.success('已退出登录')
      }
   } finally {
      logoutLoading.value = false
   }
}
onMounted(async()=>{
   request.setAuthFailureHandler(handleAuthFailure)
   try {
      const result = await ChatAiApi.refreshSessionApi()
      const authUser = result?.data?.user
      if (!authUser) {
         handleAuthFailure()
         return
      }
      applyAuthenticatedUser(authUser)
      authStatus.value = 'authenticated'
      await nextTick()
      await loadAuthenticatedData()
   } catch {
      handleAuthFailure()
   }
})
const updateTitleMessage = async (message) => {
    leftmenuRef.value?.updateTitleMessage(message)
}
const updateChatMessage = (data) => {
    chatcontainerRef.value?.updateChatMessage(data)
}
const loadAuthenticatedData = async ()=> {
    await configRef.value?.updateUserModelConfig() 
    //获取到用户的最新的会话记录，不过滤modelconfigid user.modelconfigid
    const result = await ChatAiApi.getConversationByUserIdApi(user.userid)
    if(result?.code == 200) {
        const data = result.data
        if(!data) return 
        await leftmenuRef.value?.updateChatList(data)
    }
}
const updateUserModelConfig = async ()=> {
    authStatus.value = 'authenticated'
    await nextTick()
    await loadAuthenticatedData()
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
.auth_bootstrap {
    width: 100vw;
    height: 100vh;
    background-color: #FFFFFF;
}
</style>
