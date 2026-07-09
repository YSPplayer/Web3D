<template>
    <div class ='container flex_row'>
        <leftmenu/>
    </div>

</template>
<script setup>
import leftmenu from './component/leftmenu.vue';
</script>
<style scoped>
.leftmenu {
    width: 15%;
    height: 100%;
    background-color: #FFFFFF;
    border-right: 1px solid #ccc;
}
.container {
    background-color: #FFFFFF;
    /*vw,相对于浏览器窗口的变化尺寸*/
    width: 100vw; 
    height: 100vh;
}    
</style>