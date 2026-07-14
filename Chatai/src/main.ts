import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import { request } from '@/api/request'
import 'element-plus/dist/index.css'
const apiUrl = import.meta.env.VITE_SERVER_API_URL;
request.create(apiUrl) //初始化接口
const app = createApp(App)
app.use(ElementPlus).mount('#app')
