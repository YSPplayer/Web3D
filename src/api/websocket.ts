import { ElMessage } from 'element-plus'
import WebProcess from './webprocess'
import {WebSocketPackage,SocketType} from "../data"
export default class WebSocketClient {
    private url:string
    private socket: WebSocket | null
    private backFunctions:Map<string, Function>
    private isconnect:boolean
    private intervalId:number
   constructor(url: string) {
      this.url = url;
      this.socket = null;
      this.backFunctions = new Map();
      this.isconnect = false;
      this.intervalId = 0;
   }
   onopen(event: Event) {
        console.log("WebSocket连接成功:", event);
        ElMessage.success("WebSocket连接成功");
        this.startHeartbeat();//启动心跳机制
        if(this.backFunctions.has("onopen")) {
            this.backFunctions.get("onopen")?.(event);
        }
   }
   onmessage(event: MessageEvent) {
        if(event.data instanceof Blob) {
            if(this.backFunctions.has("onmessage")) {
                WebProcess.handleBinaryMessage(event.data)
               // this.backFunctions.get("onmessage")?.(event);
            }
        }
   }
   onclose(event: Event) {
        if(this.backFunctions.has("onclose")) {
            this.backFunctions.get("onclose")?.(event);
        }
   }
   onerror(event: Event) {
        if(this.backFunctions.has("onerror")) {
            this.backFunctions.get("onerror")?.(event);
        }
   }
   sendMessageBinary(data:WebSocketPackage) {
        if(!this.isCoonnect()) return;
        const buffer = WebProcess.createBinaryMessage(data)
        this.socket?.send(buffer);
   }
   sendMessage(code:number) {
        if(!this.isCoonnect()) return;
         const data: WebSocketPackage = {
            version: WebProcess.CLIENT_VERSION,
            code: code,
            size: 0,
            length: [],
            context:[]
        };
        this.sendMessageBinary(data);
   }
   isCoonnect() {
        return this.isconnect && this.socket !== null;
   }
   disconnect() {
    if (this.socket) { //断开连接
        this.socket.close();
        this.socket = null;
        this.isconnect = false;
    }
   }
   //启动心跳机制
   startHeartbeat(time:number = 10000) { 
        if(!this.isCoonnect()) return;
       this.intervalId = setInterval(() => {
            //给服务器发送消息
            this.sendMessage(SocketType.CLIENT_TO_SERVER_HEART_BEAT);
        }, time); 
   }
   //停止心跳机制
   stopHeartbeat() { 
        clearInterval(this.intervalId);
   }
   connect() {
    try {
        this.socket = new WebSocket(this.url);
        this.socket.binaryType = "arraybuffer"; //设置二进制数据类型
        this.socket.onopen = this.onopen.bind(this);
        this.socket.onmessage = this.onmessage.bind(this);
        this.socket.onclose = this.onclose.bind(this);
        this.socket.onerror = this.onerror.bind(this);
        this.isconnect = true;
    }catch(error) {
        this.isconnect = false;
        console.error("WebSocket连接异常:", error);
        ElMessage.error("WebSocket连接异常" + error);
    }
   }
} 