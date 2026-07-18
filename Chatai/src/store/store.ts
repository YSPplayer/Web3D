import { reactive } from 'vue'
export interface User {
    userid:number
    modelconfigid:number,
    conversationsid:Array<number>
    username:string
}

export const user = reactive<User>({
    userid: -1,
    conversationsid:[],
    modelconfigid:-1,
    username: ""
})