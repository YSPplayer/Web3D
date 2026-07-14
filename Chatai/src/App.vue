<template>
    <div class ='container flex_row'>
        <leftmenu/>
        <chatcontainer/>
    </div>
    <login ref="loginRef"/>
</template>
<script setup>
import leftmenu from './component/leftmenu.vue';
import chatcontainer from './component/chatcontainer.vue';
import login from './component/login.vue'
import { ref, onMounted } from 'vue'
const loginRef = ref(null)
onMounted(()=>{
    if (loginRef.value) {
        loginRef.value.openDialog()
    }
})
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