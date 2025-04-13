import { Shader } from "../Shader/shader.js";
export class Model {
    constructor() {
        this._modelAttribute = null; // 模型属性
        this._shader = new Shader(); // 模型着色器对象
        this._vao = null; // 对VAO进行统一管理的对象
        this._vbos = []; // 顶点缓冲对象数组
        this._datas = []; // 存放所有类型渲染数据的容器
        this._hasTexture = false; // 是否有贴图
        this._empty = true; // 当前模型是否有数据
    }
    
    dispose() {
        this._vbos.forEach(vbo => {
            if (vbo !== null) gl.deleteBuffer(1,vbo);
        });
        if(this._vao !== null) Util.deleteVertexArray(this._vao);
        this._empty = true;
    }

    //virtual
    render(data, lightControl, camera) {}

    //virtual
    resetPosition() {}

    isEmpty() {
        return this._empty;
    }

    hasTexture() {
        return this._hasTexture;
    }


    getVBOData(type) {
        if (this._empty || type >= this._datas.length) return null;
        return this._datas[type];
    }

    static createEmptyModel() {
        return new Model();
    }


    updateAttribute(data) {
        // 更新属性逻辑
    }

    // 绑定缓冲对象
    static bindBufferObject(oID, bufferType, data, dataSize, attributeIndex, componentsPerVertex, usage = gl.STATIC_DRAW) {
        const empty = oID === null;
        // 生成并绑定 VBO
        if (empty) {
            oID = gl.createBuffer();
        }
        // 设置当前 VBO 上下文
        gl.bindBuffer(bufferType, oID);
        // 先绑定空指针，避免显存溢出的问题
        if (empty) {
            gl.bufferData(bufferType, dataSize * Float32Array.BYTES_PER_ELEMENT, usage);
        }
        // 持久映射 CPU 缓冲区到 GPU 数据指针
        if (data != null) {
            const buffer = gl.mapBufferRange(bufferType, 0, dataSize * Float32Array.BYTES_PER_ELEMENT, gl.MAP_WRITE_BIT);
            if (!buffer) {
                console.error("绑定缓冲对象错误：GPU映射失败！");
                return false; // 检查映射是否成功
            }
            // 复制数据到缓冲区
            new Float32Array(buffer).set(data);
            gl.unmapBuffer(bufferType); // 取消映射
        }
        if (bufferType === gl.ARRAY_BUFFER) {
            gl.vertexAttribPointer(attributeIndex, componentsPerVertex, gl.FLOAT, false, componentsPerVertex * Float32Array.BYTES_PER_ELEMENT, 0);
            gl.enableVertexAttribArray(attributeIndex); // 启用顶点属性
        }
        const error = gl.getError();
        if (error !== gl.NO_ERROR) {
            console.error("WebGL错误：", error);
            return false;
        }
        return true;
    }
}
