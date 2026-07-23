import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import { katex } from '@mdit/plugin-katex'

import 'highlight.js/styles/github.css'
import 'katex/dist/katex.min.css'

const COPY_ICON = `
<svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
>
    <rect x="9" y="9" width="11" height="11" rx="2"></rect>
    <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"></path>
</svg>
`

const DOWNLOAD_ICON = `
<svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
>
    <path d="M12 3v12"></path>
    <path d="m7 10 5 5 5-5"></path>
    <path d="M5 21h14"></path>
</svg>
`

const markdown = new MarkdownIt({
    html: false,
    linkify: true,
    breaks: true
})

markdown.use(katex, {
    delimiters: 'all',
    throwOnError: false,
    strict: false
})

const languageAliases: Record<string, string> = {
    js: 'javascript',
    ts: 'typescript',
    py: 'python',
    sh: 'bash',
    shell: 'bash',
    'c++': 'cpp',
    'c#': 'csharp'
}

markdown.renderer.rules.fence = (tokens, index) => {
    const token = tokens[index]

    const originalLanguage =
        token.info.trim().split(/\s+/)[0].toLowerCase() ||
        'text'

    const highlightLanguage =
        languageAliases[originalLanguage] ||
        originalLanguage

    const safeLanguage =
        markdown.utils.escapeHtml(originalLanguage)

    const safeHighlightLanguage =
        markdown.utils.escapeHtml(highlightLanguage)

    let codeHtml: string

    if (
        highlightLanguage !== 'text' &&
        hljs.getLanguage(highlightLanguage)
    ) {
        codeHtml = hljs.highlight(token.content, {
            language: highlightLanguage,
            ignoreIllegals: true
        }).value
    } else {
        codeHtml = markdown.utils.escapeHtml(
            token.content
        )
    }

    // pre 与 code 之间不要添加空格或换行
    return [
        `<div class="code_block" data-language="${safeLanguage}">`,
            '<div class="code_toolbar">',
                `<span class="code_language">${safeLanguage}</span>`,
                '<div class="code_actions">',
                    '<button',
                        ' type="button"',
                        ' class="code_action_button"',
                        ' data-code-action="copy"',
                        ' title="复制代码"',
                        ' aria-label="复制代码"',
                    '>',
                        COPY_ICON,
                        '<span>复制</span>',
                    '</button>',
                    '<button',
                        ' type="button"',
                        ' class="code_action_button"',
                        ' data-code-action="download"',
                        ' title="下载代码"',
                        ' aria-label="下载代码"',
                    '>',
                        DOWNLOAD_ICON,
                        '<span>下载</span>',
                    '</button>',
                '</div>',
            '</div>',
            `<pre class="hljs"><code class="language-${safeHighlightLanguage}">${codeHtml}</code></pre>`,
        '</div>'
    ].join('')
}

function normalizeMarkdown(source: string): string {
    return source.replace(
        /([\u4e00-\u9fa5])(\*\*)(?=["“‘])/g,
        '$1 $2'
    )
}

function normalizeMath(source: string): string {
    return source.replace(
        /(^|[^!\\])\[\s*([^\]\n]*\\[a-zA-Z]+[^\]\n]*)\s*\](?!\()/g,
        (_, prefix, body) => `${prefix}$$${body}$$`
    )
}

export function renderMarkdown(source: string): string {
    const normalized = normalizeMath(
        normalizeMarkdown(source || '')
    )
    const html = markdown.render(normalized)

    return DOMPurify.sanitize(html)
}
