

export default class WebProcess {
    static readonly CLIENT_VERSION :number= 1330
    static HandleBinaryMessage(data:Blob) {
        const reader = new FileReader()
        reader.onload = function() {
            this.ParseBinaryMessage(reader.result)
        }
        reader.readAsArrayBuffer(data)
    }
    static ParseBinaryMessage(buffer:ArrayBuffer,isLittleEndian:boolean = true) {
        const view = new DataView(buffer);
        let offset = 0;
        const version = view.getInt32(offset, isLittleEndian);
        offset += 4;
        const code = view.getInt32(offset, isLittleEndian);
        offset += 4;
        return { 'version': version, 'code': code }
    }
}