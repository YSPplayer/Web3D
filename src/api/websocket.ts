import { ElMessage, Message } from 'element-plus'
export default class WebSocketClient {
    private url:string
    private socket: WebSocket | null
    private backFunctions:Map<string, Function>
   constructor(url: string) {
      this.url = url;
      this.socket = null;
      this.backFunctions = new Map();
   }
   onopen(event: Event) {
        console.log("WebSocket连接成功:", event);
        ElMessage.success("WebSocket连接成功");
        if(this.backFunctions.has("onopen")) {
            this.backFunctions.get("onopen")?.(event);
        }
   }
   onmessage(event: MessageEvent) {
        if(event.data instanceof Blob) {
            if(this.backFunctions.has("onmessage")) {
                this.backFunctions.get("onmessage")?.(event);
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
   disconnect() {
    if (this.socket) { //断开连接
        this.socket.close();
        this.socket = null;
    }
   }
   connect() {
    try {
        this.socket = new WebSocket(this.url);
        this.socket.binaryType = "arraybuffer"; //设置二进制数据类型
        this.socket.onopen = this.onopen.bind(this);
        this.socket.onmessage = this.onmessage.bind(this);
        this.socket.onclose = this.onclose.bind(this);
        this.socket.onerror = this.onerror.bind(this);
    }catch(error) {
        console.error("WebSocket连接异常:", error);
        ElMessage.error("WebSocket连接异常" + error);
    }
   }
} 