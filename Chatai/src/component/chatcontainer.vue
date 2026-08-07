<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main" v-loading="isLoding" >
            <div ref="chatMainRef" class="chat_main_container flex_colum"
            @wheel.passive="handleChatWheel"
            @scroll.passive="handleChatScroll"
            >
                <!-- <div class="loding_more" v-if="showLoadMore"> 
                    <span  @click="lodingShowMore">▲加载更多</span>
                    </div> -->
                <chatrolecontainer
                v-for="message in messages"
                :key="message.id"
                :isUser="message.role === 'user'"
                :message="message.content"
                :reasoning="message.reasoning"
                :enableReasoning="isMessageReasoning(message)"
                :streaming="message.streaming"
                :timeText="message.timeText"
                :chatName="getChatName(message.role,message.modelid)"
                :svgChat = "getSvg(message.role,message.modelid) "
                :showloding="message.showloding"
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
                <textarea  v-model="inputChatText" @keydown.enter.exact.prevent ="handleEnter()">
                </textarea>
            </div>
            <img class="chat_post" :src="generating ? stopChat : postChat" :class="fill_img"
            @click="generating ? stopChatMessage() : sendChatMessage() " >
            </img>
        </div>
    </div>
</template>

<script setup>
 import postChat from "@/assets/post.svg";
 import stopChat from "@/assets/stop.svg";
 import { ref,reactive,nextTick   } from 'vue'
 import {user} from '@/store/store'
 import { Util } from "@/shared/util";
 import {ChatAiApi} from '@/api/api'
 import { ArrowDown } from '@element-plus/icons-vue'
 import chatrolecontainer  from "@/component/chatrolecontainer.vue";
 import { ca } from "element-plus/es/locales.mjs";
 const emits = defineEmits(['updateTitleMessage']) 
 const inputChatText = ref('')
 const chatMainRef = ref(null)
 const messages = ref([])
 const isLoding = ref(false)
 const showLoadMore = ref(false)
 const showScrollBtn = ref(false)
 const autoFollow = ref(true) // 是否自动跟随最新消息
 // 距离底部小于这个值，认为用户已经到底部
 const BOTTOM_DISTANCE = 40
 const TOP_DISTANCE = 10
 const minLoadingTime = 300 //最小加载时间
 const canScroll = () => {
    const element = chatMainRef.value
    if (!element) {
        return false
    }

    return element.scrollHeight > element.clientHeight + 1
}
const handleEnter = (event) => {
  if (generating.value) return
  sendChatMessage()
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

const isAtTop = () => {
    const element = chatMainRef.value
    if (!element) {
        return true
    }
    return element.scrollTop <= TOP_DISTANCE 
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
const sleep = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms))
}
const lodingShowMore = async () => {
    const conversationid = user.conversationid
    const conversation = user.conversations[user.conversationid]
    if(!conversation.hasmore || isLoding.value) return
    isLoding.value = true
    const startTime = Date.now()
    const result = await ChatAiApi.getChatMessagePageApi(user.conversationid,user.pagenumber,conversation.pagenextid)
    if(result.code == 200 && user.conversationid === conversationid) {
        const element = chatMainRef.value
        const oldScrollHeight = element ? element.scrollHeight : 0
        const data = result.data
        conversation.pagenextid = data.next_before_id
        conversation.hasmore = data.has_more
        updateChatMessage(data.messages,true)
        nextTick(() => {
            const element = chatMainRef.value
            if (element) {
                const newScrollHeight = element.scrollHeight
                element.scrollTop = newScrollHeight - oldScrollHeight
            }
            showLoadMore.value = conversation.hasmore && canScroll() && isAtTop() 
        })
    }
    const elapsed = Date.now() - startTime
    const remain = minLoadingTime - elapsed
    if (remain > 0) {
            await sleep(remain)
    }
    isLoding.value = false
}
const handleChatScroll = async () => {
    const hasmore = user.conversations[user.conversationid].hasmore
    autoFollow.value = isAtBottom()
    showScrollBtn.value = canScroll() && !autoFollow.value
    showLoadMore.value =  hasmore && canScroll() && isAtTop() 
    if(showLoadMore.value)  {
       await lodingShowMore()
    } 
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
 const updateChatMessage = (data,insert = false) => {
    let oldmessages = []
    if(insert) oldmessages = [...messages.value]
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
    if(oldmessages.length > 0) {
        oldmessages.forEach((item) => {
        messages.value.push({
            id: lastid + 1,
            role:item.role,
            content:item.content,
            timeText:item.timeText,
            modelid:item.modelid
        })
        lastid = lastid + 1
        })
    } else {
        scrollToBottom(true)
    }
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
 const isReasoningModel = (modelid = user.modelid) => {
    const model = user.models.find(item => item.id === modelid)
    const modelName = model?.model_name || (modelid === user.modelid ? user.modelname : '') || ''
    return /(^|[-_])r1($|[-_])|reason|thinking/i.test(modelName)
}
const isMessageReasoning = (message) => {
    return Boolean(message.reasoning) || isReasoningModel(message.modelid)
}
 const handleThinkDelta = (message, delta) => {
    const openTag = '<think>'
    const closeTag = '</think>'
    let text = delta || ''

    while (text) {
        const lower = text.toLowerCase()

        if (message.inThink) {
            const closeIndex = lower.indexOf(closeTag)
            if (closeIndex === -1) {
                message.reasoning += text
                text = ''
            } else {
                message.reasoning += text.slice(0, closeIndex)
                text = text.slice(closeIndex + closeTag.length)
                message.inThink = false
            }
            continue
        }

        const openIndex = lower.indexOf(openTag)
        const closeIndex = lower.indexOf(closeTag)

        if (openIndex !== -1 && (closeIndex === -1 || openIndex < closeIndex)) {
            message.answer += text.slice(0, openIndex)
            text = text.slice(openIndex + openTag.length)
            message.inThink = true
            continue
        }

        if (closeIndex !== -1) {
            message.reasoning += message.answer + text.slice(0, closeIndex)
            message.answer = text.slice(closeIndex + closeTag.length)
            message.inThink = false
            text = ''
            continue
        }

        message.answer += text
        text = ''
    }

    message.content = message.answer
}
 const stopChatMessage = ()=> {
    if(abortController) {
        abortController.abort()
        abortController = null
    }
    generating.value = false
 }
 //生成总结性会话标题
const getTitleMessage = async ()=> {
    let title = ''
    try {
        await ChatAiApi.createChatMessageApi({
            userid: user.userid,
            modelconfigid: user.modelconfigid,
            conversationid:user.conversationid,
            message:'基于上面的对话生成一个此次会话的简短的总结性的标题，只需要文字，不需要有任何其他的符号',
            istiTle:true
        },
        event => {
            if (event.type === 'delta') {
                title += event.content
            } else if(event.type === 'done') {

            } else if(event.type === 'error') {
                title = ''
            }
        }
    )
    } catch(error) {
        title = ''
    } 
    return title
}
 const sendChatMessage = async () => {
    const userContent = inputChatText.value.trim()
    if (!userContent || generating.value) return
    const userMessage = reactive({
        id: lastid + 1,
        role: 'user',
        content: userContent,
        modelid: user.modelid,
    })
   messages.value.push(userMessage) //增加用户对话
   const reasoningEnabled = isReasoningModel(user.modelid)
   const aiMessage = reactive({
        id: lastid + 2,
        role: 'assistant',
        content: '',
        reasoning: '',
        answer: '',
        inThink: reasoningEnabled,
        reasoningEnabled,
        streaming: true,
        modelid: user.modelid,
        showloding:true
    })
    messages.value.push(aiMessage)
    scrollToBottom(true)
    inputChatText.value = ''
    generating.value = true
    abortController = new AbortController()
    try {
        await ChatAiApi.createChatMessageApi(
            {
                userid: user.userid,
                modelconfigid: user.modelconfigid,
                conversationid:user.conversationid,
                message: userContent,
                istiTle:false
            },
            event => {
                if (event.type === 'delta') {
                    if (aiMessage.reasoningEnabled) {
                        handleThinkDelta(aiMessage, event.content)
                    } else {
                        aiMessage.content += event.content
                    }
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
    } catch(error) {
        if (error.name === 'AbortError') {
            return
        }
    } finally {
        const conversation =  user.conversations[user.conversationid]
        if(conversation && conversation.isnew) {
            conversation.isnew = false
            const titlemessage = await getTitleMessage()
            if(titlemessage !== '') {
                await emits('updateTitleMessage',titlemessage)
            }
        }
        generating.value = false
        aiMessage.streaming = false
        aiMessage.showloding = false
        abortController = null
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

.chat_main_container .loding_more span {
    display: block; /*行元素转块元素*/
    width: 100%;
    text-align: center;
    color: #409EFF;
}
.chat_main_container .loding_more span:hover {
    color:rgb(240, 173, 78);
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

.chat_input textarea {
    width: calc(100% - 1.2rem);
    height: calc(100% - 1.2rem);
    margin: 0.6rem;

    border: none;
    outline: none;
    resize: none;

    color: #1f2328;
    background: transparent;

    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        "Microsoft YaHei",
        sans-serif;
    font-size: 1rem;
    line-height: 1.75;

    overflow-wrap: anywhere;
    word-break: break-word;
}
</style>
