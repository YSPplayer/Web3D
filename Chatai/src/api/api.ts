import { request } from './request'
interface UserRegister {
    username:string
    password:string
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
  }
}
