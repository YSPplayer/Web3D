import { Model } from "./model.js";
class planemodel extends Model {
    constructor() {
        this.modelAttribute = null; // 模型属性
        this._shader = null; // 模型着色器对象
        this._vao = null; // 对VAO进行统一管理的对象
        this._vbos = []; // 顶点缓冲对象数组
        this._datas = []; // 存放所有类型渲染数据的容器
        this._hasTexture = false; // 是否有贴图
        this._empty = true; // 当前模型是否有数据
    }
}