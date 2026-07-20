<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main">
            <div class="chat_main_container flex_colum">
                <chatrolecontainer :isUser="false"/>
                 <chatrolecontainer :isUser="true" />
            </div>
        </div>
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
 import chatrolecontainer  from "@/component/chatrolecontainer.vue";
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
.chat_main .chat_main_container  {
    margin-top: 1.5rem;
    margin-left: 1rem;
    margin-right: 1rem;
    gap: 1.5rem;
}
.chat_input {
    flex: 1;
    height: 100%;
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