import { reactive } from 'vue'
export interface Conversation { //会话对象
    pagenextid:number,//下一页的起始索引
    hasmore:boolean,//是否还有下一页的数据
    isnew:boolean,//是否为新建的对话
}
export interface User {
    localmodelstate:string //当前的本地模型状态
    userid:number //用户名
    userlogo:string //用户图像
    modelname:string //当前默认激活的模型名称
    modelconfigid:number, //模型配置id
    modeltype:string,//模型名称
    modellogo:string,//模型的图像
    models:Array<any>,//存储的model对象
    modelid:number, //当前激活的model对象的id
    conversationsid:Array<number> //所有会话id
    conversationid:number //激活的会话id
    username:string //用户名称
    pagenumber:number //单页查询的数量
    conversations:Map<number,Conversation>//会话数据
}

export const user = reactive<User>({
    localmodelstate:'',
    userid: -1,
    conversationsid:[],
    userlogo:'',
    modeltype:'',
    models:[], 
    modellogo:'',
    modelname:'',
    modelid: -1,
    modelconfigid:-1,
    conversationid:-1,
    username: '',
    pagenumber:20,
    conversations:new Map()
})