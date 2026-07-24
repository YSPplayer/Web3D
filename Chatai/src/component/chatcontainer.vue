<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main">
            <div ref="chatMainRef" class="chat_main_container flex_colum"
            @wheel.passive="handleChatWheel"
            @scroll.passive="handleChatScroll"
            >
                <chatrolecontainer
                v-for="message in messages"
                :key="message.id"
                :isUser="message.role === 'user'"
                :message="message.content"
                :timeText="message.timeText"
                :chatName="getChatName(message.role,message.modelid)"
                :svgChat = "getSvg(message.role,message.modelid) "
                />
            </div>
            <div v-show="showScrollBtn"  class="flex_row_center scroll_bottom_btn">
                <el-button
                    type="primary"
                    circle
                    size="large"
                    @click="scrollToBottom(true)">
                    <el-icon><ArrowDown /></el-icon>
                </el-button>
                <span @click="scrollToBottom(true)">回到底部</span>
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
 import { ref,reactive,nextTick   } from 'vue'
 import {user} from '@/store/store'
 import { Util } from "@/shared/util";
 import {ChatAiApi} from '@/api/api'
 import { ArrowDown } from '@element-plus/icons-vue'
 import chatrolecontainer  from "@/component/chatrolecontainer.vue";
 const inputChatText = ref('')
 const chatMainRef = ref(null)
 const messages = ref([])
 const showScrollBtn = ref(false)
 const autoFollow = ref(true) // 是否自动跟随最新消息
 // 距离底部小于这个值，认为用户已经到底部
 const BOTTOM_DISTANCE = 40
 const canScroll = () => {
    const element = chatMainRef.value
    if (!element) {
        return false
    }

    return element.scrollHeight > element.clientHeight + 1
}
 const isAtBottom = () => {
    const element = chatMainRef.value
    if (!element) {
        return true
    }
    const distanceToBottom =
        element.scrollHeight -
        element.scrollTop -
        element.clientHeight
    return distanceToBottom <= BOTTOM_DISTANCE
}
const handleChatWheel = event => {
    if (!canScroll()) {
        autoFollow.value = true
        showScrollBtn.value = false
        return
    }

    if (event.deltaY < 0) {
        autoFollow.value = false
        showScrollBtn.value = true
    }
}

const handleChatScroll = () => {
    autoFollow.value = isAtBottom()
    showScrollBtn.value = canScroll() && !autoFollow.value
}
 //让当前的滚动的位置始终处于底层
 const scrollToBottom = (force = false) => {
    // 用户主动发送消息时，可以强制重新开启跟随
    if (force) {
        autoFollow.value = true
        showScrollBtn.value = false
    }
    if (!autoFollow.value) {
        return
    }
    nextTick(() => {
        // nextTick 执行前用户可能已经向上滚动，因此再次判断
        if (!autoFollow.value) {
            return
        }
        const element = chatMainRef.value
        if (!element) {
            return
        }
        element.scrollTop = element.scrollHeight
        showScrollBtn.value = canScroll() && !isAtBottom()
    })
}
 const generating = ref(false)
 let abortController = null;
 const lastid = messages.value.length > 0 ?
 messages.value[messages.value.length - 1].id : 0
 const updateChatMessage = (data) => {  
    messages.value = []
    let lastid = 0
    data.forEach((item) => {
       messages.value.push({
           id: lastid + 1,
           role:item.role,
           content:item.content,
           timeText:Util.extractTime(item.created_at),
           modelid:item.model_id
       })
       lastid = lastid + 1
    })
    scrollToBottom(true)
 }
 const getChatName = (role,id)=> {
    if(role === 'user') return user.username
    const model = user.models.find(item => item.id === id)
    return `聊天助手[${model.model_name}]`
 }
  const getSvg = (role,id)=> {
    if(role === 'user') return user.userlogo
    const model = user.models.find(item => item.id === id)
    return model.logo_path
 }
 const sendChatMessage = async () => {
    const userContent = inputChatText.value.trim()
    if (!userContent || generating.value) return
    const userMessage = reactive({
        id: lastid + 1,
        role: 'user',
        content: userContent,
        modelid: user.modelid
    })
   messages.value.push(userMessage) //增加用户对话
   const aiMessage = reactive({
        id: lastid + 2,
        role: 'assistant',
        content: '',
        streaming: true,
        modelid: user.modelid
    })
    messages.value.push(aiMessage)
    scrollToBottom(true)
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
                    userMessage.timeText = Util.extractTime(event.user_created_at)
                    aiMessage.timeText =  Util.extractTime(event.ai_created_at)
                } else if (event.type === 'error') {
                    aiMessage.streaming = false
                    aiMessage.content ||= event.message
                }
                scrollToBottom()
            },
            abortController.signal
        )
    } finally {
        generating.value = false
        aiMessage.streaming = false
    }
 } 
 defineExpose({
    updateChatMessage
 })
</script>

<style scoped>
.chatcontainer {
    gap:1rem;
}
.scroll_bottom_btn {
    position: absolute;  /* 添加：脱离文档流 */
    bottom: 1rem;        /* 添加：距离底部 */
    right: 1rem;         /* 添加：距离右侧 */
    margin: 0;           /* 修改：移除原有 margin */
    z-index: 10;
    gap: 0.5rem;
}
.scroll_bottom_btn span {
    color: #409EFF;
}

.scroll_bottom_btn:hover {
    cursor: pointer;
}

.scroll_bottom_btn:hover span {
    color:rgb(240, 173, 78);
}
.chat_main {
    position: relative;
    margin-top: 1rem;
    width: 95%;
    /* 自动占用剩余高度 */
    flex: 1; 
    border: 1px solid #ccc;
    border-radius: 10px;
    /* 允许 flex 子元素收缩 */
    min-height: 0;
    /* 内容不能撑开外层 */
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.chat_main .chat_main_container  {
    margin-top: 1.5rem;
    margin-left: 1rem;
    margin-right: 1rem;
    gap: 1.5rem;

    flex: 1;
    min-height: 0;
    
 /* 保留滚轮滚动 */
    overflow-x: hidden;
    overflow-y: auto;

    /* Firefox 隐藏滚动条 */
    scrollbar-width: none;

    /* 旧版 IE、Edge */
    -ms-overflow-style: none;

    /* 移动端惯性滚动 */
    -webkit-overflow-scrolling: touch;

    /* 防止滚动传递给整个页面 */
    overscroll-behavior: contain;
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
.chat_post:hover {
   cursor: pointer;
}

/* Chrome、Edge、Safari 隐藏滚动条 */
.chat_main_container::-webkit-scrollbar {
    display: none;
    width: 0;
    height: 0;
}
</style>
