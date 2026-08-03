import { request } from './request'
interface UserRegister {
    username:string
    password:string
    imgurl:string
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

interface ChatMessage {
  userid: number
  modelconfigid: number
  conversationid: number
  message: string
  istiTle:boolean
}

type ChatStreamEvent =
  | { type: 'delta'; content: string }
  | { type: 'done' }
  | { type: 'error'; message: string }

export const ChatAiApi = {
  //post
  async userRegisterApi(user: UserRegister): Promise<any> {
    
    return await request.post('/chatai/register', user)
  },
  async userLoginApi(user: UserRegister): Promise<any> {
    return await request.post('/chatai/login', user)
  },
  async createConversationApi(conversation:Conversation) : Promise<any> {
    return await request.post('/chatai/user/conversation',conversation)
  },
  async createChatMessageApi(data:ChatMessage,
    onEvent:(event:ChatStreamEvent)=>void,signal?: AbortSignal) {
    const apiUrl = import.meta.env.VITE_SERVER_API_URL.replace(/\/$/, '')
    const response = await fetch(
      `${apiUrl}/chatai/user/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data),
        signal
      }
    )
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
