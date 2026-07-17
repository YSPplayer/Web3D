<template>
    <div class ='container flex_row'>
        <leftmenu @showConfigDialog= 'showConfigDialog'  />
        <chatcontainer/>
    </div>
    <login ref="loginRef" @updateUserModelConfig = 'updateUserModelConfig'/>
    <config ref="configRef"/>
</template>
<script setup>
import leftmenu from './component/leftmenu.vue';
import chatcontainer from './component/chatcontainer.vue';
import login from './component/login.vue'
import config from './component/config.vue'
import { ref, onMounted } from 'vue'
const loginRef = ref(null)
const configRef = ref(null)
const showConfigDialog = ()=>{
   configRef.value?.openDialog()
}
onMounted(()=>{
   loginRef.value?.openDialog()
})
const updateUserModelConfig = async ()=> {
    await configRef.value?.updateUserModelConfig() 
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