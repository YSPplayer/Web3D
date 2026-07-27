import { reactive } from 'vue'
export interface User {
    userid:number //用户名
    userlogo:string //用户图像
    modelconfigid:number, //模型配置id
    modeltype:string,//模型名称
    modellogo:string,//模型的图像
    models:Array<any>,//存储的model对象
    modelid:number, //当前激活的model对象的id
    conversationsid:Array<number> //所有会话id
    conversationid:number //激活的会话id
    username:string //用户名称
    pagenumber:number //单页查询的数量
    pagenextids:Map<number,number> //下一页的起始索引
    hasmores:Map<number,boolean> //是否还有下一页的数据
}

export const user = reactive<User>({
    userid: -1,
    conversationsid:[],
    userlogo:'',
    modeltype:'',
    models:[], 
    modellogo:'',
    modelid: -1,
    modelconfigid:-1,
    conversationid:-1,
    username: '',
    pagenumber:20,
    pagenextids:new Map(),
    hasmores:new Map()
})