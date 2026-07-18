import { request } from './request'
interface UserRegister {
    username:string
    password:string
}
interface ModelConfig {
    userid:number
    modeltype:string
    modelname:string
    apikey:string
    isonline:number
}

interface Conversation {
   userid: number,
   modelconfigid: number,
   title: string
}
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


  //put
  async saveModelConfigApi(config: ModelConfig):Promise<any> {
    return await request.put('/chatai/saveModelConfig',config)
  },
  
  //get
  async modelsApi():Promise<any> {
    return await request.get('/chatai/models')
  },
  async getUserModelConfigApi(userid:number):Promise<any> {
    return await request.get('/chatai/user/modelConfg',{
    params: { userid }
  })
  },
  async getModelConfigState(userid:number,modeltype:string,modelname:string):Promise<any> {
    return await request.get('/chatai/user/modelConfgState',{
    params: { userid,modeltype,modelname }
  })
  },
  async getConversationApi(userid: number,modelconfigid: number):Promise<any> {
    return await request.get('/chatai/user/getConversation',
      {params:{userid,modelconfigid}}
    )
  },

}
