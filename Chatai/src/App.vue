<template>
    <div class ='container flex_row'>
        <leftmenu/>
        <chatcontainer/>
    </div>

</template>
<script setup>
import leftmenu from './component/leftmenu.vue';
import chatcontainer from './component/chatcontainer.vue';
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