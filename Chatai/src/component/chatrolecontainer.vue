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
                            <span>{{timeText}}</span>
                    </div>
                  <div class="chat_message markdown_body"
                    v-html="renderedMessage"
                     @click="handleMarkdownClick">
                  
                </div>
                </div>    
            </div>
        </div>
    </div>
</template>

<script setup>
 import svgChat from "@/assets/chat.svg";
 import { computed } from 'vue'
 import { renderMarkdown } from '@/shared/markdown'
 import { ElMessage } from 'element-plus'
 const props = defineProps({
    isUser: {
        type: Boolean,
        default: false
    },
    message:{
        type:String,
        default:''
    },
    timeText: {
        type:String,
        default:''
    }
})
const renderedMessage = computed(() => {
    return renderMarkdown(props.message)
})
const extensionMap = {
    javascript: 'js',
    js: 'js',
    typescript: 'ts',
    ts: 'ts',
    python: 'py',
    py: 'py',
    cpp: 'cpp',
    'c++': 'cpp',
    c: 'c',
    java: 'java',
    csharp: 'cs',
    'c#': 'cs',
    json: 'json',
    html: 'html',
    css: 'css',
    bash: 'sh',
    shell: 'sh',
    sql: 'sql',
    vue: 'vue',
    text: 'txt'
}

const copyText = async text => {
    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {
        await navigator.clipboard.writeText(text)
        return
    }
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    const success =
        document.execCommand('copy')

    textarea.remove()
    if (!success) {
        throw new Error('复制失败')
    }
}

const downloadText = (text, language) => {
    const extension =
        extensionMap[language] || 'txt'
    const blob = new Blob(
        [text],
        {
            type: 'text/plain;charset=utf-8'
        }
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download =
        `snippet-${Date.now()}.${extension}`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => {
        URL.revokeObjectURL(url)
    }, 100)
}

const handleMarkdownClick = async event => {
    const target = event.target

    if (!(target instanceof Element)) {
        return
    }

    const button = target.closest(
        '.code_action_button'
    )

    if (!button) {
        return
    }

    const codeBlock =
        button.closest('.code_block')

    const codeElement =
        codeBlock?.querySelector('code')

    if (!codeElement) {
        ElMessage.error('没有找到代码内容')
        return
    }

    const action =
        button.getAttribute('data-code-action')

    const language =
        codeBlock.getAttribute('data-language') ||
        'text'

    const code = codeElement.textContent || ''

    if (action === 'copy') {
        try {
            await copyText(
                code.replace(/\n$/, '')
            )

            ElMessage({
                message: '代码已复制',
                type: 'success',
                duration: 1300
            })
        } catch (error) {
            console.error('复制代码失败：', error)

            ElMessage({
                message: '复制失败，请手动复制',
                type: 'error',
                duration: 1800
            })
        }

        return
    }

    if (action === 'download') {
        try {
            downloadText(code, language)

            ElMessage({
                message: '代码已下载',
                type: 'success',
                duration: 1300
            })
        } catch (error) {
            console.error('下载代码失败：', error)

            ElMessage({
                message: '代码下载失败',
                type: 'error',
                duration: 1800
            })
        }
    }
}
</script>
<style scoped>
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


.chat_role_context .chat_role_span {
    gap:0.5rem;
}
.chat_role_container .chat_role_img {
    height: 2.403125rem;
    aspect-ratio: 1 / 1;  /*宽高相等*/
    object-fit: fill; 
}

.chat_message {
    min-width: 0;
    max-width: 100%;

    line-height: 1.75;
    overflow-wrap: anywhere;
    word-break: break-word;

    user-select: text;
    -webkit-user-select: text;
    cursor: text;
}

/* Markdown 自己控制段落和换行 */
.markdown_body {
    white-space: normal;
}

/* 段落 */
.markdown_body :deep(p) {
    margin: 0.6rem 0;
}

/* 第一个和最后一个元素不产生多余边距 */
.markdown_body :deep(> :first-child) {
    margin-top: 0;
}

.markdown_body :deep(> :last-child) {
    margin-bottom: 0;
}

/* 标题 */
.markdown_body :deep(h1),
.markdown_body :deep(h2),
.markdown_body :deep(h3),
.markdown_body :deep(h4) {
    margin: 1rem 0 0.6rem;
    line-height: 1.4;
    font-weight: 600;
}

.markdown_body :deep(h1) {
    font-size: 1.5rem;
}

.markdown_body :deep(h2) {
    font-size: 1.3rem;
}

.markdown_body :deep(h3) {
    font-size: 1.15rem;
}

/* 列表 */
.markdown_body :deep(ul),
.markdown_body :deep(ol) {
    margin: 0.6rem 0;
    padding-left: 1.8rem;
}

.markdown_body :deep(li) {
    margin: 0.3rem 0;
}

/* 行内代码 */
.markdown_body :deep(:not(pre) > code) {
    padding: 0.15rem 0.35rem;

    color: #c7254e;
    background: #f3f4f6;
    border-radius: 4px;

    font-family: Consolas, Monaco, monospace;
    font-size: 0.9em;
}

/* 代码块 */
.markdown_body :deep(pre) {
    max-width: 100%;
    margin: 0.8rem 0;
    padding: 1rem;

    overflow-x: auto;

    background: #f6f8fa;
    border: 1px solid #e5e7eb;
    border-radius: 8px;

    white-space: pre;
}

.markdown_body :deep(pre code) {
    padding: 0;
    background: transparent;

    font-family: Consolas, Monaco, monospace;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* 引用块 */
.markdown_body :deep(blockquote) {
    margin: 0.8rem 0;
    padding: 0.4rem 1rem;

    color: #606770;
    background: #f8f9fa;
    border-left: 4px solid #d0d7de;
}

/* 分割线 */
.markdown_body :deep(hr) {
    margin: 1rem 0;
    border: none;
    border-top: 1px solid #e5e7eb;
}

/* 表格 */
.markdown_body :deep(table) {
    display: block;
    width: 100%;
    margin: 0.8rem 0;

    overflow-x: auto;
    border-collapse: collapse;
}

.markdown_body :deep(th),
.markdown_body :deep(td) {
    padding: 0.5rem 0.75rem;
    border: 1px solid #dfe2e5;
    text-align: left;
}

.markdown_body :deep(th) {
    background: #f6f8fa;
}

/* 链接 */
.markdown_body :deep(a) {
    color: #1677ff;
    text-decoration: none;
}

.markdown_body :deep(a:hover) {
    text-decoration: underline;
}

/* 数学公式过宽时允许横向滚动 */
.markdown_body :deep(.katex-display) {
    max-width: 100%;
    margin: 0.8rem 0;
    padding: 0.25rem 0;

    overflow-x: auto;
    overflow-y: hidden;
}
/* 只负责把按钮放到工具栏右侧 */
.markdown_body :deep(.code_toolbar) {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* 复制、下载按钮区域 */
.markdown_body :deep(.code_actions) {
    display: inline-flex;
    align-items: center;
    gap: 6px;

    user-select: none;
    -webkit-user-select: none;
}

/* DeepSeek 风格无边框按钮 */
.markdown_body :deep(.code_action_button) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;

    height: 28px;
    padding: 0 6px;

    color: #60656f;
    background: transparent;
    border: none;
    border-radius: 6px;

    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    font-size: 13px;
    line-height: 1;

    cursor: pointer;

    transition:
        color 0.15s ease,
        background-color 0.15s ease;
}

.markdown_body :deep(.code_action_button:hover) {
    color: #25282d;
    background-color: rgba(0, 0, 0, 0.055);
}

.markdown_body :deep(.code_action_button:active) {
    background-color: rgba(0, 0, 0, 0.095);
}

.markdown_body :deep(.code_action_button:focus-visible) {
    outline: 2px solid rgba(64, 128, 255, 0.35);
    outline-offset: 1px;
}

/* 复制、下载 SVG */
.markdown_body :deep(.code_action_button svg) {
    width: 15px;
    height: 15px;
    flex-shrink: 0;

    pointer-events: none;
}

/* 避免点击文字时影响按钮定位 */
.markdown_body :deep(.code_action_button span) {
    pointer-events: none;
}
</style>

