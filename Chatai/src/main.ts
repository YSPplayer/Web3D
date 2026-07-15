import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import { request } from '@/api/request'
import { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
const apiUrl = import.meta.env.VITE_SERVER_API_URL;
request.create(apiUrl) //初始化接口
request.get('/chatai/health').then(()=>{
    ElMessage.success(`HTTP服务器${apiUrl}连接成功！`)
}).catch(()=> {
    ElMessage.error(`HTTP服务器${apiUrl}连接失败！`)
})
const app = createApp(App)
app.use(ElementPlus).mount('#app')
