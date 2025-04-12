class ModelKeyPoint {//模型关键点
    constructor() {
        this.position = glMatrix.mat4.create();//默认的模型矩阵，用于控制模型的位置和方向
        this.centerPosition = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);//模型的中心位置
        this.changeCenterPosition = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);//模型变化的中心位置
        this.minPosition = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);//模型包围盒中三个坐标轴上的最小点
        this.maxPosition = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);//模型包围盒中三个坐标轴的最大点
        this.wposition = glMatrix.mat4.create();
        this.modelSize = 1.0;//模型的最大尺寸，用于缩放
        this.lightRadius = 0.0;//模型距离点光源位置的半径
    }
}
class ModelAttribute { //模型属性
    constructor() { 
        this.keyPoint = new ModelKeyPoint();
    }
}
// class PlaneModelBuildData {
//     constructor() {
//         this.vertices = []; 
//     }

// }

class LineModelBuildData {
    constructor() {
        this.vertices = []; 
        this.modelAttribute = new ModelAttribute();    
    }

}

const VBOType = Object.freeze({
    Vertex: 0,    // 顶点索引
    Texture: 1,   // 贴图索引
    Normal: 2,    // 法线索引
    Mapcolor: 3,  // 伪彩色贴图索引
    Wall: 4,      // 墙面数组
    Flag: 5,      // 存储标签位，记录丢弃点
    Index: 6,     // 存储索引位，存放每一个点的索引
    Max: 7
});

export { ModelKeyPoint, ModelAttribute,LineModelBuildData,VBOType};