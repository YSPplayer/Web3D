export class ModelKeyPoint {//模型关键点
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

    copy() {
        const copy = new ModelKeyPoint();
        glMatrix.mat4.copy(copy.position, this.position);
        glMatrix.vec3.copy(copy.centerPosition, this.centerPosition);
        glMatrix.vec3.copy(copy.changeCenterPosition, this.changeCenterPosition);
        glMatrix.vec3.copy(copy.minPosition, this.minPosition);
        glMatrix.vec3.copy(copy.maxPosition, this.maxPosition);
        glMatrix.mat4.copy(copy.wposition, this.wposition);
        copy.modelSize = this.modelSize;
        copy.lightRadius = this.lightRadius;
        return copy;
    }
}
export class ModelAttribute { //模型属性
    constructor() { 
        this.keyPoint = new ModelKeyPoint();
    }
  
    copy() {
        const copy = new ModelAttribute();
        copy.keyPoint = this.keyPoint.clone();
        return copy;
    }
}
export class Material {
    constructor(ambient, diffuse, specular, shininess) {
        // 环境光照色
        this.ambient = ambient ? glMatrix.vec3.clone(ambient) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 漫反射颜色，控制模型表面颜色
        this.diffuse = diffuse ? glMatrix.vec3.clone(diffuse) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 镜面高光的颜色，控制模型亮度
        this.specular = specular ? glMatrix.vec3.clone(specular) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 光的散射半径
        this.shininess = shininess !== undefined ? shininess : 0.0;
    }

    equals(other) {
        return glMatrix.vec3.equals(this.ambient, other.ambient) && 
               glMatrix.vec3.equals(this.diffuse, other.diffuse) &&
               glMatrix.vec3.equals(this.specular, other.specular) && 
               this.shininess === other.shininess;
    }

    copy() {
        return new Material(
            this.ambient,
            this.diffuse,
            this.specular,
            this.shininess
        );
    }
}
export class Color {
    constructor(r, g, b) {
        this.r = r;
        this.g = g;
        this.b = b;
    }
    redF() {
        return this.r / 255;
    }
    greenF() {
        return this.g / 255;
    }
    blueF() {
        return this.b / 255;
    }
}
export class LightAttribute {
    constructor() {
        this.position = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 平行光方向[写死]
        this.direction = glMatrix.vec3.fromValues(-0.2, -1.0, -0.3);
        // 光照材质
        this.material = new Material();
        // 非线性常量1（常数项衰减因子）
        this.constant = 1.0;
        // 非线性常量2（一次项衰减因子）
        this.linear = 0.09;
        // 非线性常量3（二次项衰减因子）
        this.quadratic = 0.032;
        // 当前光照的半径范围
        this.lightRadius = 1.0;
    }
}
export class CameraAttribute {
    constructor() {
        this.front =  glMatrix.vec3.create(); // 默认为[0,0,0]
        // 相机的世界坐标系位置
        this.position = glMatrix.vec3.create(); // 默认为[0,0,0]
        // 前方向和后方向计算的结果向量
        this.right = glMatrix.vec3.create(); // 默认为[0,0,0]
        // 世界坐标系的上方向向量，固定不变
        // 根据这个向量与Z方向向量叉乘，可以得到X轴的方向向量【写死】
        this.worldUp = glMatrix.vec3.create(); // 默认为[0,0,0]
        // 相机的视角向量，表示相机的本地上方向
        this.up = glMatrix.vec3.create(); // 默认为[0,0,0]
        // 相机视角的观察矩阵
        // 对于任意世界坐标系中的模型，都可以转换到这个位置中
        this.view = glMatrix.mat4.create(); // 默认为单位矩阵
        // 透视或平行视口
        this.projection = glMatrix.mat4.create(); // 默认为单位矩阵
    }
}
export class LineModelBuildData {
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

export { VBOType };