export const Util = {
    extractTime(datetimeStr:string) {
        return datetimeStr.slice(11, 16)
    },
    isEmptyObject(obj:any) {
        return obj && typeof obj === 'object' && Object.keys(obj).length === 0
    },
    stringToBase64(str:string):string {
        // 1. 将字符串转为 UTF-8 编码的 URL 安全字符串
        const encoded = encodeURIComponent(str)
        // 2. 将 %XX 格式转为原始字节（还原为二进制字符串）
        const binary = encoded.replace(/%([0-9A-F]{2})/g, (match, hex) => {
            return String.fromCharCode(parseInt(hex, 16))
        })
        // 3. 编码为 Base64
        return btoa(binary)
    },
    base64ToString(base64:string):string {
    // 1. 解码 Base64 为二进制字符串
    const binary = atob(base64)
    // 2. 将二进制字符串转为 Uint8Array
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
    }
    // 3. 用 TextDecoder 解码为 UTF-8 字符串
    const decoder = new TextDecoder()
    return decoder.decode(bytes)
}


};                                                              