import { reactive } from 'vue'
export interface User {
    userid:number
    username:string
}

export const user = reactive<User>({
    userid: -1,
    username: ""
})