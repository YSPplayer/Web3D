<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main">
            <div class="chat_main_container flex_colum">
                <chatrolecontainer
                v-for="message in messages"
                :key="message.id"
                :is-user="message.role === 'user'"
                :message="message.content"
                />
            </div>
        </div>
        <div class="chat_input_container flex_row">
            <div class="chat_input">
                <textarea  v-model="inputChatText">
                </textarea>
            </div>
            <img class="chat_post" :src="postChat" :class="fill_img"
            @click="sendChatMessage">

            </img>
        </div>
    </div>
</template>

<script setup>
 import postChat from "@/assets/post.svg";
 import { ref,reactive  } from 'vue'
 import {user} from '@/store/store'
 import {ChatAiApi} from '@/api/api'
 import chatrolecontainer  from "@/component/chatrolecontainer.vue";
 const inputChatText = ref('')
 const messages = ref([])
 const generating = ref(false)
 let abortController = null;
 const lastid = messages.value.length > 0 ?
 messages.value[messages.value.length - 1].id : 0
 const sendChatMessage = async () => {
    const userContent = inputChatText.value.trim()
    if (!userContent || generating.value) return
    messages.value.push({  //增加用户的会话
        id: lastid + 1,
        role: 'user',
        content: userContent
    })
   const aiMessage = reactive({
        id: lastid + 2,
        role: 'assistant',
        content: '',
        streaming: true
    })
    messages.value.push(aiMessage)
    inputChatText.value = ''
    generating.value = true
    abortController = new AbortController()
    try {
        await ChatAiApi.create_chat_messageApi(
            {
                userid: user.userid,
                modelconfigid: user.modelconfigid,
                conversationid:user.conversationid,
                message: userContent
            },
            event => {
                if (event.type === 'delta') {
                    aiMessage.content += event.content
                } else if (event.type === 'done') {
                    aiMessage.streaming = false
                } else if (event.type === 'error') {
                    aiMessage.streaming = false
                    aiMessage.content ||= event.message
                }
            },
            abortController.signal
        )
    } finally {
        generating.value = false
        aiMessage.streaming = false
    }
 } 
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