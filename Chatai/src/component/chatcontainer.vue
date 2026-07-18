<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main"></div>
        <div class="chat_input_container flex_row">
            <div class="chat_input">
                <textarea  v-model="inputChatText">
                </textarea>
            </div>
            <img class="chat_post" :src="postChat" :class="fill_img">

            </img>
        </div>
    </div>
</template>

<script setup>
 import postChat from "@/assets/post.svg";
 import { ref } from 'vue'
 const inputChatText = ref('')
</script>

<style scoped>
.chatcontainer {
    gap:1rem;
}
.chat_main {
    margin-top: 1rem;
    width: 95%;
    /* 自动占用剩余高度 */
    flex: 1; 
    border: 1px solid #ccc;
    border-radius: 10px;
}
.chat_input {
    flex: 1;
    height: 100%;
}
.chat_input textarea::-webkit-scrollbar {
    width: 7px;
    background: transparent;
}

/* 滚动条背景轨道 */
.chat_input textarea::-webkit-scrollbar-track {
    background: transparent;
}

/* 滚动滑块 */
.chat_input textarea::-webkit-scrollbar-thumb {
    min-height: 30px;
    border-radius: 999px;
    background-color: rgba(100, 100, 100, 0.45);
    background-clip: padding-box;
}

/* 鼠标移动到滑块 */
.chat_input textarea::-webkit-scrollbar-thumb:hover {
    background-color: rgba(100, 100, 100, 0.65);
}

/* 取消顶部和底部箭头 */
.chat_input textarea::-webkit-scrollbar-button,
.chat_input textarea::-webkit-scrollbar-button:single-button,
.chat_input textarea::-webkit-scrollbar-button:vertical:start:decrement,
.chat_input textarea::-webkit-scrollbar-button:vertical:end:increment {
    display: none;
    width: 0;
    height: 0;
    min-height: 0;
    background: transparent;
    background-image: none;
    -webkit-appearance: none;
}

/* 右下角区域透明 */
.chat_input textarea::-webkit-scrollbar-corner {
    background: transparent;
}
.chat_input textarea {
    width: calc(100% - 1.2rem);
    height: calc(100% - 1.2rem);
    margin-left: 0.6rem;
    margin-top: 0.6rem;
    /* ===== 取消默认边框 ===== */
    border: none;
    outline: none;  /* 取消聚焦时的外发光（Chrome/Safari） */
    /* ===== 禁止调整大小 ===== */
    resize: none;
    font-size: 20px; 
    /* ===== 文本方向：从左到右 ===== */
    direction: ltr; 
}   
.chat_input_container {
     width: 95%;
     height: 7.375rem;
     border-radius: 10px;
     border: 1px solid #ccc;
     margin-bottom: 1rem;
}
.chat_post {
    margin-top: auto;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    width: 2.5rem;
    height: 2.5rem;
}
</style>