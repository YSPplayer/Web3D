<template>
<div class="leftmenu flex_colum">
    <div class="chat_title flex_row">
        <img :src="svgChat" alt="聊天图标">
        <span> 智能聊天助手 </span>
    </div>
    <el-button type="primary">+ 新建对话</el-button>
    <el-input placeholder="搜索对话">
        <template #prefix>
            <el-icon><Search /></el-icon>
        </template>
    </el-input>
    <div class="chat_menu">

    </div>
    <div class="chat_config flex_colum">
        <div class="chat_line"></div>
        <div></div>
    </div>
</div>
</template>
<script setup>
 import svgChat from "@/assets/chat.svg";
 import { Search } from '@element-plus/icons-vue'
</script>
<style scoped>
.leftmenu {
     align-items: center; 
     gap: 0.625rem;
}
.chat_title img {
    height: 100%;
    aspect-ratio: 1 / 1;  /*宽高相等*/
    object-fit: fill; 
}
.chat_title span {
    display: grid;
    place-items: center; 
    font-size: 1.1rem;
    font-weight: 600;
    margin-left: 0.625rem;
}
.chat_title {
    margin-top: 0.625rem;
    width: 90%;
    height: 3%; 
    align-items: center; 
}
/* 让vue不加data=xxx，因为饿了么ui默认这个类名不加data，否则样式找不到 */
:deep(.el-button),
:deep(.el-input){ 
    width: 90%;
    height: 2.8%;
}
.chat_menu {
    flex: 1; /* 撑满剩余空间 */
    width: 100%;
    height: auto;

}
.chat_line {
    width: 90%;
    height: 1px;
    background-color: #CCCCCC;
}
.chat_config {
    margin-top: auto;
    width: 100%;
    height: 5%;
    align-items: center; 
}
</style>
