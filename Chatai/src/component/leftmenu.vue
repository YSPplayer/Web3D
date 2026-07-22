<template>
<div class="leftmenu flex_colum">
    <div class="chat_title flex_row">
        <img :src="svgChat" alt="聊天图标">
        <span> 智能聊天助手 </span>
    </div>
    <el-button type="primary" @click="newChatButton" style="height: 35.89px;">+ 新建对话</el-button>
    <el-input placeholder="搜索对话" style="height: 35.89px;">
        <template #prefix>
            <el-icon><Search /></el-icon>
        </template>
    </el-input>
    <div class="chat_menu scroll_container flex_colum">
         <div 
            v-for="(item, index) in chatList" 
            :key="item.id"
            class="chat_box flex_row_center"
            :class="{'chat_box_activate': activeId
                 === item.id 
            }"
            @click="selectChat(item.id,index)"
        >
            <span> {{item.name}} </span>
            <el-button v-if="activeId
                 === item.id "  type="primary"class='chat_box_button_delete'
                 @click = "deleteSelectChat(item.id,index)">
                <el-icon><Delete /></el-icon>
            </el-button>
        </div>
    </div>
    <div class="chat_config flex_colum">
        <div class="chat_line"></div>
        <div class="chat_config_user flex_row">
            <div class="user_img"></div>
            <span>{{userName}}</span>
            <div class="user_edit flex_row_center" @click="showConfigDialog">
                <img :src="editChat" class="fill_img" />
            </div>
        </div>
    </div>
</div>
</template>
<script setup>
 import svgChat from "@/assets/chat.svg";
 import editChat from "@/assets/edit.svg";
 import { Search } from '@element-plus/icons-vue'
 import {defineEmits,ref,watch } from 'vue'
 import {user} from '@/store/store'
 import { ChatAiApi } from "@/api/api";
 import { Delete } from '@element-plus/icons-vue'
 import { ElMessageBox, ElMessage } from 'element-plus'
 const userName = ref('')
 const chatList = ref([])
 const activeId = ref(chatList.value[0]?.id || null)
 const emits = defineEmits(['showConfigDialog','updateChatMessage'])
 const showConfigDialog = ()=> {
    emits('showConfigDialog')
 }
 const deleteSelectChat = async (id,index) => {
    ElMessageBox.confirm('是否删除当前会话？','提示',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
        }
    ).then(async ()=>{
        const result = await ChatAiApi.deleteCconversationApi(user.conversationid)
    if(result.code == 200) {
        ElMessage.success('会话删除成功！')
        //删除掉对应的会话
        chatList.value = chatList.value.filter(item => item.id !== id)
        user.conversationsid = user.conversationsid.filter(item => item !== user.conversationid)
        const newindex = Math.min(index,chatList.value.length - 1)
        const newid = chatList.value[newindex].id
        await selectChat(newid,newindex)
    }   
    })
 }

 const selectChat = async (id,index) => {
    if(activeId.value === id) return 
    activeId.value = id
    user.conversationid = user.conversationsid[index]
    await updateChatMessage()
}
 const newChatButton = async ()=> {
    const newtitle = '新对话'
    const result =  await ChatAiApi.createConversationApi({
        userid : user.userid,
        modelconfigid : user.modelconfigid,
        title : newtitle
    }
    ) 
    if(result.code == 200) {
        const data = result.data
        user.conversationsid.push(data.conversationid)
        pushValueToChatList(newtitle)
    }
 }
const pushValueToChatList = (value)=> {
  const lastid = chatList.value.length > 0 ?
        chatList.value[chatList.value.length - 1].id 
            : 0
  chatList.value.push({
            id: lastid + 1,
            name:value
        })
}
const updateChatList = async (data)=> {
    chatList.value = []
    user.conversationsid = []
    data.forEach((item) => {
        user.conversationsid.push(item.id)
       pushValueToChatList(item.title)
    })
    if(chatList.value.length <= 0) return
    //默认激活第一个会话
    activeId.value = 1
    user.conversationid = user.conversationsid[0]
    await updateChatMessage()
}
const updateChatMessage = async ()=> {
    //获取到当前默认会话id下的聊天记录  
    const result = await ChatAiApi.getChatMessageApi(user.conversationid)
    if(result.code == 200) {
        const data = result.data
        emits('updateChatMessage',data)
    }
}
watch(() => user.username,(newName) => {
       userName.value = newName
    }
)
defineExpose({
  updateChatList
})
</script>
<style scoped>
.chat_box_activate {
   border: 1px solid #409EFF;
   background-color: rgba(239,246,255, 0.5);
}
.chat_box:not(.chat_box_activate):hover {
    background-color: #F1F3F5
}
.chat_box:hover {
    cursor: pointer;
}
.chat_box {
   width: calc(100% - 2rem);
   height: 40px;
   flex: 0 0 45px;
   border-radius: 3px;
   margin: 0 1rem;
}
.chat_menu .chat_box span {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    margin-left: 1rem;
}
.chat_box .chat_box_button_delete {
    width: 35px;
    height: 35px;
    /* margin-right: 1px; */
      /* 去除背景和边框 !important 强制生效 */
    background: transparent !important;
    border: none !important;
    /* 让按钮只占图标大小 */
    padding: 4px;
    min-width: auto;
    width: 32px;
    height: 32px;
    
    /* 让图标居中 */
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

/* 图标默认颜色（灰色） */
.chat_box_button_delete .el-icon {
  font-size: 20px;
  color: #909399;
}
.chat_box_button_delete:hover .el-icon {
     color: #409EFF;
}
.leftmenu {
     align-items: center; 
     gap: 0.625rem;
}
.chat_config_user {
    width: 100%;
    gap: 0.625rem;
}
.user_edit:hover {
   cursor: pointer;
}
.user_edit {
    width:1.8rem;
    aspect-ratio: 1 / 1;
    margin-left: auto;
    margin-right: 1.5rem;
}
.chat_title img {
    height: 2.403125rem;
    aspect-ratio: 1 / 1;  /*宽高相等*/
    object-fit: fill; 
}
.chat_config .flex_row {
     align-items: center; 
}
.user_img {
    border-radius: 50%;
    width: 2.6rem;
    aspect-ratio: 1 / 1;
    background-color: #409EFF;
    margin-left: 1rem;
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
    min-height: 0;
    /* gap:0.5rem; */
    height: auto;
    align-items: center; 

}
.chat_line {
    width: 90%;
    height: 1px;
    background-color: #CCCCCC;
}
.chat_config {
    gap: 0.625rem;
    margin-top: auto;
    width: 100%;
    align-items: center; 
    margin-bottom: 0.5rem;
}
</style>
