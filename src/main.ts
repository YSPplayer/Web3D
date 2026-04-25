import { createApp } from "vue";
import ElementPlus from "element-plus";

import App from "@/App.vue";
import "@/styles.css";
import "element-plus/dist/index.css";
import { request } from '@/api/request'
const apiUrl = import.meta.env.VITE_SERVER_API_URL;
request.create(apiUrl) //初始化接口
createApp(App).use(ElementPlus).mount("#app");
