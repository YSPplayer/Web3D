import { reactive } from 'vue'
export interface User {
    userid:number
    modelconfigid:number,
    username:string
}

export const user = reactive<User>({
    userid: -1,
    modelconfigid:-1,
    username: ""
})