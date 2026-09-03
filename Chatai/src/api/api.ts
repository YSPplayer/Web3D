import { request } from './request'
interface UserRegister {
    username:string
    password:string
    imgurl:string
}
interface UserLogin {
    username:string
    password:string
}
interface ModelConfig {
    userid:number
    modeltype:string
    modelname:string
    apikey:string
    isonline:number
    proxyhost:string
    proxyport:number
    proxyactive:number
}

interface Conversation {
   userid: number,
   modelconfigid: number,
   title: string
}

type ChatMode = 'chat' | 'agent'

export interface AgentTraceItem {
  id: string
  kind: 'tool'
  toolName: string
  command: string
  status: 'running' | 'success' | 'failed' | 'denied' | 'timeout'
  summary: string
}

export interface AgentTool {
  id: number
  tools_name: string
  display_name: string
  description: string
  risk_level: 'low' | 'medium' | 'high'
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface AgentToolPage {
  items: AgentTool[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

interface ChatMessage {
  userid: number
  modelconfigid: number
  conversationid: number
  message: string
  istiTle:boolean
  mode: ChatMode
}

type ChatStreamEvent =
  | {
      type: 'meta'
      request_id: string
      assistant_message_id: number
      assistant_created_at: string
      user_created_at: string
    }
  | { type: 'delta'; content: string }
  | {
      type: 'agent_trace'
      action: 'start' | 'finish'
      trace: AgentTraceItem
    }
  | {
      type: 'agent_error'
      code: string
      message: string
      tool_name?: string
      run_id?: number | null
      requested_capability?: string
      missing_fields?: string[]
    }
  | {
      type: 'done'
      user_created_at: string
      ai_created_at: string
      assistant_message_id: number
      status: 'completed'
    }
  | { type: 'error'; message: string }

export const ChatAiApi = {
  //post
  async startLocalModelApi(userid:number, modelconfigid:number) {
    return request.post(`/chatai/localModel/start?userid=${userid}&modelconfigid=${modelconfigid}`)
  },
  async userRegisterApi(user: UserRegister): Promise<any> {
    
    return await request.post('/chatai/register', user)
  },
  async stopLocalModelApi() {
    return await request.post('/chatai/localModel/stop')
  },
  async userLoginApi(user: UserLogin): Promise<any> {
    const result = await request.post('/chatai/login', user)
    if (result?.data?.access_token) {
      request.setAccessToken(result.data.access_token)
    }
    return result
  },
  async refreshSessionApi(): Promise<any> {
    return request.refreshSession()
  },
  async logoutApi(): Promise<any> {
    request.beginLogout()
    try {
      return await request.post('/chatai/auth/logout')
    } finally {
      request.finishLogout()
    }
  },
  async createConversationApi(conversation:Conversation) : Promise<any> {
    return await request.post('/chatai/user/conversation',conversation)
  },
  async stopChatMessageApi(userid: number, requestid: string) {
    return request.post(
      `/chatai/user/chat/stop?userid=${userid}&requestid=${encodeURIComponent(requestid)}`
    )
  },
  async createConversationTitleApi(userid:number, conversationid:number): Promise<any> {
    return await request.post('/chatai/user/conversation/title', {
      userid,
      conversationid
    })
  },
  async createChatMessageApi(data:ChatMessage,
    onEvent:(event:ChatStreamEvent)=>void,signal?: AbortSignal) {
    const apiUrl = import.meta.env.VITE_SERVER_API_URL.replace(/\/$/, '')
    const sendRequest = () => fetch(
        `${apiUrl}/chatai/user/chat`,
        {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${request.getAccessToken()}`
        },
        body: JSON.stringify(data),
        signal,
        credentials: 'include'
        }
    )
    let response = await sendRequest()
    if (response.status === 401) {
      await request.refreshSessionOrLogout()
      response = await sendRequest()
    }
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `HTTP ${response.status}`)
    }
    if (!response.body) {
      throw new Error('浏览器不支持流式响应')
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        buffer += decoder.decode()
        break
      }

      buffer += decoder.decode(value, {
        stream: true
      })

      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.trim()) continue

        const event = JSON.parse(line) as ChatStreamEvent
        onEvent(event)
      }
    }
    if (buffer.trim()) {
      onEvent(JSON.parse(buffer))
    }
  },
  //delete
  async deleteCconversationApi(conversationid:number):Promise<any> {
    return await request.delete('/chatai/user/conversation', {
      params: { conversationid }
    })
  },
  //put
  async saveModelConfigApi(config: ModelConfig):Promise<any> {
    return await request.put('/chatai/saveModelConfig',config)
  },
  
  //get
  async getSystemMetricsApi() {
    return await request.get('/chatai/system/metrics')
  },
  async getAgentToolsPageApi(page: number, pageSize: number): Promise<any> {
    return await request.get('/chatai/agent/tools', {
      params: {
        page,
        page_size: pageSize
      }
    })
  },
  async getDefaultUserImageApi(): Promise<any> {
    return await request.get('/chatai/user/defaultUserImage')
  },
  async getTokensCountApi(conversationid: number, date: string): Promise<any> {
  return await request.get('/chatai/user/tokensCount', {
    params: {
      conversationid,
      date
    }
  })
  },
  async getLocalModelStatusApi() {
    return await request.get('/chatai/localModel/status')
  },
  async getTokensCountByUserIdApi(userid: number, date: string): Promise<any> {
  return await request.get('/chatai/user/tokensCountByUserId', {
    params: {
      userid,
      date
    }
  })
  },
  async modelsApi():Promise<any> {
    return await request.get('/chatai/models')
  },
  async getUserModelConfigApi(userid:number):Promise<any> {
    return await request.get('/chatai/user/modelConfg',{
    params: { userid }
  })
  },
  async getModelConfigStateApi(userid:number,modeltype:string,modelname:string):Promise<any> {
    return await request.get('/chatai/user/modelConfgState',{
    params: { userid,modeltype,modelname }
  })
  },
  async getConversationApi(userid: number,modelconfigid: number):Promise<any> {
    return await request.get('/chatai/user/getConversation',
      {params:{userid,modelconfigid}}
    )
  },
  async getConversationByUserIdApi(userid: number):Promise<any> {
    return await request.get('/chatai/user/getConversationByUserId',
      {params:{userid}}
    )
  },
  async getChatMessageApi(conversationid:number):Promise<any> {
      return await request.get('/chatai/user/chatMessages',
      {params:{conversationid}}
    )
  },
  async getChatMessagePageApi(conversationid:number,limit:number,beforeid:number):Promise<any> {
          return await request.get('/chatai/user/chatPageMessages',
      {params:{conversationid,limit,beforeid}}
    )
  }


}
