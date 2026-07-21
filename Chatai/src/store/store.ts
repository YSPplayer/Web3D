import { reactive } from 'vue'
export interface User {
    userid:number //用户名
    userlogo:string //用户图像
    modelconfigid:number, //模型配置id
    modeltype:string,//模型名称
    modellogo:string,//模型的图像
    conversationsid:Array<number> //所有会话id
    conversationid:number //激活的会话id
    username:string //用户名称
}

export const user = reactive<User>({
    userid: -1,
    conversationsid:[],
    userlogo:'',
    modeltype:'',
    modellogo:'',
    modelconfigid:-1,
    conversationid:-1,
    username: ''
})