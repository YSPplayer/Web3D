<template>
    <div>
        <div 
        :class="[
            {'chat_role_container':true},
            {'flex_row': true},
            {'chat_role_reverse':isUser},
        ]   ">
            <img :src="svgChat" class="chat_role_img">
            <div class="chat_role_context">
                <div class ="chat_role_context_mr flex_colum">
                    <div class="chat_role_span flex_row">
                            <span class="chat_role_span_title">助手</span>
                            <span>09:30</span>
                    </div>
                  <div class="chat_message">
                     {{ message }}
                  </div>
                </div>    
            </div>
        </div>
    </div>
</template>

<script setup>
 import svgChat from "@/assets/chat.svg";

 const props = defineProps({
    isUser: {
        type: Boolean,
        default: false
    },
    message:{
        type:String,
        default:''
    }
})
</script>
<style>
.chat_role_container {
    gap: 1rem;
    width: 100%;
}
.chat_role_reverse {
    justify-content: flex-start;
    flex-direction: row-reverse;
}
.chat_role_span_title {
     font-weight: bold;
}
.chat_role_context_mr {
    margin:0.73rem;
    gap: 0.5rem;

}
.chat_role_context {
    width: fit-content;
    max-width: 70%;
    border-radius: 5px;
    background-color: #F9FAFB;
    border: 1px solid #EAEDF0;

}

.chat_message {
    text-indent: 2em;  /* 缩进 2 个字符 */
    width: fit-content; /*宽度根据内容自适应*/
    height: auto; /*高度自动撑开*/
    white-space: pre-wrap; /*保留空格和换行，同时允许自动换行*/
    overflow-wrap: anywhere;/*长单词/URL 可以在任意位置折断换行*/
    word-break: break-word; /*单词内部可以折断换行*/
}
.chat_role_context .chat_role_span {
    gap:0.5rem;
}
.chat_role_container .chat_role_img {
    height: 2.403125rem;
    aspect-ratio: 1 / 1;  /*宽高相等*/
    object-fit: fill; 
}
</style>

