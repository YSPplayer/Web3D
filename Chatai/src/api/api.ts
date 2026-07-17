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
export const ChatAiApi = {
  //post
  async userRegisterApi(user: UserRegister): Promise<any> {
    
    return await request.post('/chatai/register', user)
  },
  async userLoginApi(user: UserRegister): Promise<any> {
    return await request.post('/chatai/login', user)
  },

  //put
  async saveModelConfigApi(config: ModelConfig):Promise<any> {
    return await request.put('/chatai/saveModelConfig',config)
  },
  
  //get
  async modelsApi():Promise<any> {
    return await request.get('/chatai/models')
  },
  async getUserModelConfigApi(userid:number) {
    return await request.get('/chatai/user/modelConfg',{
    params: { userid }
  })
  },
  async getModelConfigState(userid:number,modeltype:string,modelname:string) {
    return await request.get('/chatai/user/modelConfgState',{
    params: { userid,modeltype,modelname }
  })
  },


}
