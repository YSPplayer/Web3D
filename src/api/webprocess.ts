import {WebSocketPackage,SocketType} from "../data"
import {ElMessage} from 'element-plus'
export default class WebProcess {
    static readonly CLIENT_VERSION :number= 1330
    static handleBinaryMessage(data:Blob) {
        const reader = new FileReader()
        reader.onload = function() {
           const data =  WebProcess.parseBinaryMessage(reader.result as ArrayBuffer)
           WebProcess.handleTypeMessage(data)
        }
        reader.readAsArrayBuffer(data)
    }
    static handleTypeMessage(data:WebSocketPackage | null | undefined) {
        if(!data) return;
        // const sendData: WebSocketPackage = {
        //         version: WebProcess.CLIENT_VERSION,
        //         code: 0,
        //         size: 0,
        //         length: [],
        //         context:[]
        // };
        switch(data.code) { 
            case SocketType.SERVER_TO_CLIENT_HEART_BEAT:{
                console.log('已接收到服务器心跳机制的回复')
            }
            break;
            default:
            break;
        }
    }
    static createBinaryMessage(data:WebSocketPackage,isLittleEndian:boolean = true):ArrayBuffer {
        let totalSize = 12 //version + code + size
        if(data.size > 0) {
            data.context.forEach((element,index) => {
                totalSize += (4 + data.length[index]);  // 4字节长度 + 数据
            });
        }
         // 创建ArrayBuffer
        const buffer = new ArrayBuffer(totalSize);
        const view = new DataView(buffer);
        let offset = 0;
        view.setInt32(offset, data.version, isLittleEndian);
        offset += 4;
        view.setInt32(offset, data.code, isLittleEndian);
        offset += 4;
        view.setInt32(offset, data.size, isLittleEndian);
        offset += 4;
        if(data.size > 0) {
             data.context.forEach((element,index) => {
             view.setInt32(offset, data.length[index], isLittleEndian);//写入数据大小
             offset += 4;
             //写入buffer
            const uint8View = new Uint8Array(buffer, offset, data.length[index]);
            uint8View.set(element);
            offset += data.length[index];
            });
        }
        // this.ws.send(buffer);
        return buffer;
    }
    static parseBinaryMessage(buffer:ArrayBuffer,isLittleEndian:boolean = true):WebSocketPackage | null | undefined {
       try {
            const view = new DataView(buffer);
            const data: WebSocketPackage = {
                version: 0,
                code: 0,
                size: 0,
                length: [],
                context:[]
            };
            let offset = 0;
            data.version = view.getInt32(offset, isLittleEndian);
            offset += 4;
            data.code = view.getInt32(offset, isLittleEndian);
            offset += 4;
            data.size = view.getInt32(offset, isLittleEndian);
            if(data.size > 0){
                
            }
              return data;
        } catch (error) {
            console.error("解析二进制消息异常:", error);
            ElMessage.error("解析二进制消息异常:"+ error);
            return null;
        }
    }
}