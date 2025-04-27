import { LightType,LightPointType,PlaneModelType,MapColorType} from "../const.js";
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
export class PlaneModelKeyPoint extends  ModelKeyPoint { //平面模型关键点
    constructor() {
        super();
        //模型4个边界点
        this.topLeft = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        this.topRight = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        this.bottomLeft = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        this.bottomRight = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
    }

}
export class ModelAttribute { //模型属性
    constructor() { 
        this.keyPoint = new ModelKeyPoint();
    }
  
    copy() {
        const copy = new ModelAttribute();
        copy.keyPoint = this.keyPoint.copy();
        return copy;
    }
}
export class Axes {
    constructor() {
        this.increment = 0;//分辨率
        this.offset = 0;//偏移量
    }
}
export class X3pData {
    constructor() {
        this.sizeX = 0;//点云宽度数量
        this.sizeY = 0;//点云高度数量
        this.axes = Array(3).fill(null);//XYZ轴类型
        this.minZ = 0;//Z轴最小值
        this.maxZ = 0;//Z轴最大值
        this.pointData = [];//点云数据
    }

}
export class PlaneModelAttribute extends ModelAttribute {
    constructor() {
        super(); // 调用父类构造函数
        this.keyPoint = new PlaneModelKeyPoint();//平面模型关键点
        this.owidth = 0;      // 模型宽度
        this.oheight = 0;     // 模型高度
        this.sparse = false;  // 模型宽高是否因算法而稀疏
        this.width = 0.0;     // 模型实际宽度（实际宽度 = (点云宽度数量 - 1)* 分辨率）
        this.height = 0.0;    // 模型实际高度（实际高度 = (点云高度数量 - 1)* 分辨率）
        this.xincrement = 0.0; // X轴分辨率
        this.yincrement = 0.0; // Y轴分辨率
        this.maxZ = 0.0;      // 模型的实际最大Z轴高度，默认是分辨率之后的结果
        this.minZ = 0.0;      // 模型的实际最小Z轴高度，默认是分辨率之后的结果
        this.absMax = 0.0;    // 绝对最大值
        this.mtype = MapColorType.Gold; // 当前模型显示的colormap类型
        this.restoreZ = [];   // 1:1还原Z轴值
        this.rootZ = [];      // 根Z值
        // 运算参数
        this.unitStep = 0.0;
        this.cz = 0.0;
        this.xSpace = 0.0;
    }

    copy() {
        const copy = new PlaneModelAttribute();
        // 复制基类属性
        copy.keyPoint = this.keyPoint.copy();
        // 复制本类属性
        copy.owidth = this.owidth;
        copy.oheight = this.oheight;
        copy.sparse = this.sparse;
        copy.width = this.width;
        copy.height = this.height;
        copy.xincrement = this.xincrement;
        copy.yincrement = this.yincrement;
        copy.maxZ = this.maxZ;
        copy.minZ = this.minZ;
        copy.absMax = this.absMax;
        copy.mtype = this.mtype;
        copy.unitStep = this.unitStep;
        copy.cz = this.cz;
        copy.xSpace = this.xSpace;
        copy.restoreZ = [...this.restoreZ];
        copy.rootZ = [...this.rootZ];
        return copy;
    }
    
}
export class Material {
    constructor(ambient, diffuse, specular, shininess) {
        // 环境光照色
        this.ambient = ambient !== undefined  ? glMatrix.vec3.clone(ambient) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 漫反射颜色，控制模型表面颜色
        this.diffuse = diffuse !== undefined  ? glMatrix.vec3.clone(diffuse) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        // 镜面高光的颜色，控制模型亮度
        this.specular = specular !== undefined  ? glMatrix.vec3.clone(specular) : glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
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
    constructor(r, g, b, a) {
        this.r = r;
        this.g = g;
        this.b = b;
        this.a = a !== undefined ? a : 255;  
    }
    redF() {
        return this.r / 255.0;
    }
    greenF() {
        return this.g / 255.0;
    }
    blueF() {
        return this.b / 255.0;
    }
    alphaF() {
        return this.a / 255.0;
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
export class PlaneModelBuildData {
    constructor() {
        this.hasTexture = false; // 是否存储贴图
        this.vertices = []; // 顶点数组
        this.textures = []; // 贴图数组
        this.normals = []; // 法线数组 
        this.colorMaps = []; // 存放伪彩色数据
        this.walls = []; 
        this.flags = []; // 标签位数组
        this.index = []; // 存储索引位
        this.imageDatas = []; // 贴图数据的数组
        this.textureAttribute = {}; // 贴图的属性
        this.indices = []; // 顶点索引数组
        this.planeModelAttribute = new PlaneModelAttribute(); //模型数据属性
        // this.showMode = 0; 
        this.ptype = PlaneModelType.Surface; 
    }
}
export class LineModelBuildData {
    constructor() {
        this.vertices = []; 
        this.modelAttribute = new ModelAttribute();    
    }

}

export class RenderData {
    constructor() {
        this.isParallelFov = false;//是否为平行视口
        this.parallel = 0.83;//平行视口视野大小
        this.baseParallel = 0.83;//平行视口视野大小
        this.fov = Math.PI / 9.0;//视口视野大小
        this.baseFov = Math.PI / 9.0;//视口视野大小
        this.maxFov = 3.14;//最大视野大小
        this.minFov = Math.PI / 360.0;//最小视野大小
        this.lightIntensity = 1.0;//光照强度因子
        this.lightDiffuse = 1.15;//光照的漫反射因子
        this.lightAmbient = 0.2;//光照的环境光因子
        this.lightAo =1.0;//物理渲染环境光遮蔽
        this.lightMetallic = 0.556;//物理渲染金属度
        this.lightRoughness = 0.2;//物理渲染粗糙度
        this.lightPbrColorIntensity = 1.0;//物理渲染光照强度
        this.rotationZ = 0.0;//Z轴旋转角度
        this.rotationX = 0.0;//X轴旋转角度
        this.zDynamic = 3.0;//Z轴高度
        this.rotateXZ = false;//旋转XZ
        this.moveXY = false;
        this.moveX = 0.0;
        this.moveY = 0.0;
        this.adjustLight = false;//调整光照
        this.moveXLight = 0.0;//光照水平坐标
        this.moveYLight = 0.0;//光照垂直坐标
        this.width = 0;//视口高度
        this.height = 0;//视口高度
        this.sceneColor = new Color(255,255,255);
        this.lightColor = new Color(255,255,255);
        this.modelColor = new Color(255,255,255);
        this.lightType = LightType.Point;
        this.lightPointType = LightPointType.Dynamics;
        this.ptype = PlaneModelType.Surface;
        this.oldPos = { x: -99.0, y: -99.0 };
        this.newPos = { x: -99.0, y: -99.0 };
    }
}