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
    isactive:number
}
export const ChatAiApi = {
  async userRegisterApi(user: UserRegister): Promise<any> {
    
    return await request.post('/chatai/register', user)
  },
  async userLoginApi(user: UserRegister): Promise<any> {
    return await request.post('/chatai/login', user)
  },
  async modelsApi():Promise<any> {
    return await request.get('/chatai/models')
  },
  async saveModelConfigApi(config: ModelConfig):Promise<any> {
    return await request.put('/chatai/saveModelConfig',config)
  }
}
