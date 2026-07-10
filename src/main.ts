import { createApp } from "vue";
import ElementPlus from "element-plus";

import App from "@/App.vue";
import "@/styles.css";
import "element-plus/dist/index.css";
import { request } from '@/api/request'
import WebSocketClient from '@/api/websocket'
const apiUrl = import.meta.env.VITE_SERVER_API_URL;
request.create(apiUrl) //初始化接口
const webSocketClient = new WebSocketClient(import.meta.env.VITE_SERVER_WS_URL) //初始化WebSocket
webSocketClient.connect()
createApp(App).use(ElementPlus).mount("#app");
