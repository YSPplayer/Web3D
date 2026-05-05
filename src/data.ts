export const enum SocketType {
    SERVER_TO_CLIENT_HEART_BEAT = 1001,//心跳机制
    CLIENT_TO_SERVER_HEART_BEAT = 2001,//心跳机制
}
export interface WebSocketPackage {
    version:number,
    code:number,
    size:number,
    length:number[],
    context:Uint8Array[]
}

