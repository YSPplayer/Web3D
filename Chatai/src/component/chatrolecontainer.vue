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
                    <div class="chat_input">
                        <textarea>你好，有什么可以帮忙的吗？
                        </textarea>
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
    }
})
</script>
<style>
.chat_role_container {
    gap: 1rem;
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
    border-radius: 5px;
    background-color: #F9FAFB;
    border: 1px solid #EAEDF0;

}
.chat_role_context_mr .chat_input textarea {
    margin-left: 0;
    margin-top: 0;
    width: 100%;
    height: 100%;
    background-color: #F9FAFB;

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

