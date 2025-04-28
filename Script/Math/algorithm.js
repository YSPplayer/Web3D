import { PlaneModelBuildData,ModelKeyPoint} from "../Geomety/data.js";
import { GL_CONST,PlaneModelType,MapColorType } from "../const.js";
import { MapColor } from "../Geomety/colormap.js";
export class Algorithm {
    constructor() {

    }
    static getSparseSize(n, step, border) {
        // 基础稀疏宽度计算（向上取整）
        let sparseWidth = Math.ceil(n / step);
        // 检查是否需要处理边界
        border = ((n - 1) % step !== 0);
        // 如果存在边界则增加一个采样点
        if (border) sparseWidth++;
        return {sparseBorder:border,sparseSize:sparseWidth};
    }
    static getVertexCoordinates(vertices, index) {
            return glMatrix.vec3.fromValues(
                vertices[index * 3],
                vertices[index * 3 + 1],
                vertices[index * 3 + 2]
            );
    };
    // 计算面法线
    static calculateFaceNormal(v1, v2, v3) {
        const edge1 = glMatrix.vec3.create();
        const edge2 = glMatrix.vec3.create();
        const normal = glMatrix.vec3.create();
        // 计算两条边向量
        glMatrix.vec3.subtract(edge1, v2, v1);
        glMatrix.vec3.subtract(edge2, v3, v1);
        // 计算叉积
        glMatrix.vec3.cross(normal, edge1, edge2);
        return normal;
    };
    static updateNormals(vertices, vsize, indices, isize, normals, normalFactor = 1.0) {
        // 顶点数量
        const nsize = vsize / 3;
        // 创建法线数组
        const normalsv3 = new Array(nsize);
        // 初始化法线数组为零向量
        for (let i = 0; i < nsize; i++) {
            normalsv3[i] = glMatrix.vec3.fromValues(0.0, 0.0, 0.0);
        }
        // 遍历每个三角形，计算面法线并将其添加到顶点法线
        for (let i = 0; i < isize; i += 3) {
            // 获取三角形三个顶点的索引
            const idx1 = indices[i];
            const idx2 = indices[i + 1];
            const idx3 = indices[i + 2];
            
            // 获取三角形的三个顶点坐标
            const v1 = glMatrix.vec3.fromValues(
                vertices[idx1 * 3 + 0],
                vertices[idx1 * 3 + 1],
                vertices[idx1 * 3 + 2] * normalFactor
            );
            
            const v2 = glMatrix.vec3.fromValues(
                vertices[idx2 * 3 + 0],
                vertices[idx2 * 3 + 1],
                vertices[idx2 * 3 + 2] * normalFactor
            );
            
            const v3 = glMatrix.vec3.fromValues(
                vertices[idx3 * 3 + 0],
                vertices[idx3 * 3 + 1],
                vertices[idx3 * 3 + 2] * normalFactor
            );
            // 计算面法线
            const normal = Algorithm.calculateFaceNormal(v1, v2, v3);
            // 将法线添加到每个顶点
            glMatrix.vec3.add(normalsv3[idx1], normalsv3[idx1], normal);
            glMatrix.vec3.add(normalsv3[idx2], normalsv3[idx2], normal);
            glMatrix.vec3.add(normalsv3[idx3], normalsv3[idx3], normal);
        }
        
        // 归一化所有顶点法线并将其存储在输出数组中
        for (let i = 0; i < nsize; i++) {
            // 归一化法线向量
            glMatrix.vec3.normalize(normalsv3[i], normalsv3[i]);
            normals[i * 3 + 0] = normalsv3[i][0];
            normals[i * 3 + 1] = normalsv3[i][1];
            normals[i * 3 + 2] = normalsv3[i][2];
        }
    }

    static BuildPlaneModel(x3pdata) {
        let planeModelBuildData = new PlaneModelBuildData();
        planeModelBuildData.ptype = PlaneModelType.Surface;
        let width = x3pdata.sizeX - 1; //点云数量 - 1
        let height = x3pdata.sizeY - 1; //点云数量 - 1
        const xincrement = x3pdata.axes[0].increment;
        const yincrement = x3pdata.axes[1].increment;
        const xoffset = 0;//不考虑偏移量
        const yoffset = 0;//不考虑偏移量
        let pointWidth = width + 1;
        let pointHeight = height + 1;
        const maxX = pointWidth * xincrement + Math.abs(xoffset);
		const maxY = pointHeight * yincrement + Math.abs(yoffset);
		const maxZ = x3pdata.maxZ - x3pdata.minZ;
        const absMax = Math.max(maxX, maxY, maxZ);
        const pointCount = pointWidth * pointHeight; 
        const step = (pointCount > GL_CONST.ALGORITHM_MAX_POINT_SIZE) ? 2 : 1;
       const planeModelAttribute = planeModelBuildData.planeModelAttribute;
        planeModelAttribute.xincrement = xincrement;
        planeModelAttribute.yincrement = yincrement;
        planeModelAttribute.owidth = width;
        planeModelAttribute.oheight = height;
        planeModelAttribute.width = width * xincrement;
        planeModelAttribute.height = height * yincrement;
        planeModelAttribute.maxZ = x3pdata.maxZ;
        planeModelAttribute.minZ = x3pdata.minZ;
        planeModelAttribute.absMax = absMax;
        planeModelAttribute.sparse = false;
        planeModelBuildData.textures = new Float32Array(pointCount * 2);
        let zindex = 0; //顶点数据索引
        let tindex = 0; // 贴图数据索引
        const points = [];
        const indices = [];
        planeModelAttribute.keyPoint = new ModelKeyPoint();
        planeModelAttribute.keyPoint.position = glMatrix.mat4.create(); // Default model matrix
        planeModelAttribute.keyPoint.minPosition = glMatrix.vec3.fromValues(Number.MAX_VALUE, Number.MAX_VALUE, Number.MAX_VALUE);
        planeModelAttribute.keyPoint.maxPosition = glMatrix.vec3.fromValues(Number.MIN_VALUE, Number.MIN_VALUE, Number.MIN_VALUE);
        let progressStep = 0;
        const totalProgressStep = 5;
        progressStep++;
        // if (typeof CallBack !== 'undefined' && CallBack.SetModelLoadingProgress) {
        //     CallBack.SetModelLoadingProgress(progressStep, totalProgressStep);
        // }
        if (step > 1) {
            let xborder = false;
            let yborder = false;
            const xsparse = Algorithm.getSparseSize(pointWidth, step, xborder);
            const ysparse = Algorithm.getSparseSize(pointHeight, step, yborder);
            xborder = xsparse.sparseBorder;
            yborder = ysparse.sparseBorder;
            pointWidth = xsparse.sparseSize;
            pointHeight = ysparse.sparseSize;
            const sparsePointHeight = pointHeight;
            const sparsePointWidth = pointWidth;
            planeModelAttribute.owidth = pointWidth - 1;
            planeModelAttribute.oheight = pointHeight - 1;
            planeModelAttribute.width = (pointWidth - 1) * xincrement;
            planeModelAttribute.height = (pointHeight - 1) * yincrement;
            planeModelAttribute.sparse = true;
            planeModelBuildData.flags = new Float32Array(sparsePointHeight * sparsePointWidth);
            planeModelBuildData.index = new Float32Array(sparsePointHeight * sparsePointWidth);
            let findex = 0;
            for (let j = 0; j < pointHeight; j++) {
                for (let i = 0; i < pointWidth; i++) {
                    const point = { x: 0, y: 0, z: 0 };
                    let original_j = j * step;
                    let original_i = i * step;
                    if (yborder && j === sparsePointHeight - 1) {
                        original_j = height; //保留最后一行
                    }
                    if (xborder && i === sparsePointWidth - 1) {
                        original_i = width; //保留最后一列
                    }
                    
                    zindex = original_j * (width + 1) + original_i;
                    
                    if (isNaN(x3pdata.pointData[zindex])) {
                        planeModelBuildData.flags[findex] = 1.0;
                        point.z = 0.0;
                    } else {
                        planeModelBuildData.flags[findex] = 0.0;
                        point.z = x3pdata.pointData[zindex];
                    }
                    
                    planeModelBuildData.index[findex] = findex;
                    findex++;
                    
                    if (xborder && i === sparsePointWidth - 1) {
                        point.x = (width * xincrement + xoffset) / absMax;
                        planeModelBuildData.textures[tindex++] = width / width;
                    } else {
                        point.x = (i * step * xincrement + xoffset) / absMax;
                        planeModelBuildData.textures[tindex++] = (i * step) / width;
                    }
                    
                    if (yborder && j === sparsePointHeight - 1) {
                        point.y = (height * yincrement + yoffset) / absMax;
                        planeModelBuildData.textures[tindex++] = height / height;
                    } else {
                        point.y = (j * step * yincrement + yoffset) / absMax;
                        planeModelBuildData.textures[tindex++] = (j * step) / height;
                    }
                    
                    points.push(point);
                    
                    if (i < sparsePointWidth - 1 && j < sparsePointHeight - 1) {
                        indices.push([
                            i + sparsePointWidth * j,
                            i + 1 + sparsePointWidth * j,
                            i + sparsePointWidth * (j + 1)
                        ]);
                        indices.push([
                            i + 1 + sparsePointWidth * j,
                            i + 1 + sparsePointWidth * (j + 1),
                            i + sparsePointWidth * (j + 1)
                        ]);
                    }
                }
            }
        } else {
            //不启用稀疏算法
            planeModelBuildData.flags = new Float32Array(pointHeight * pointWidth);
            planeModelBuildData.index = new Float32Array(pointHeight * pointWidth);
            for (let j = 0; j < pointHeight; j++) {
                for (let i = 0; i < pointWidth; i++) {
                    const point = { x: 0, y: 0, z: 0 };
                    
                    if (isNaN(x3pdata.pointData[zindex])) {
                        planeModelBuildData.flags[zindex] = 1.0;
                        point.z = 0.0;
                    } else {
                        planeModelBuildData.flags[zindex] = 0.0;
                        point.z = x3pdata.pointData[zindex];
                    }
                    
                    planeModelBuildData.index[zindex] = zindex;
                    zindex++;
                    
                    //实际点云长度 = (索引 * (偏移量 / 最大偏移量)) /归一化值
                    point.x = (i * xincrement + xoffset) / absMax;
                    point.y = (j * yincrement + yoffset) / absMax;
                    
                    planeModelBuildData.textures[tindex++] = i / width;
                    planeModelBuildData.textures[tindex++] = j / height;
                    points.push(point);
                    if (i < width && j < height) {
                        /*
                        注意如下2次的三角形的顶点组成面的环绕顺序要保持一致，要么都是顺时针，
                        要么都是逆时针，否则计算法线会出现零向量抵消的情况
                        OpenGL的要求是逆时针右手法则，所以我们要使用逆时针，方便后续的光照等其他模式的计算
                        */
                        indices.push([
                            i + (width + 1) * j,
                            i + 1 + (width + 1) * j,
                            i + (width + 1) * (j + 1)
                        ]);
                        indices.push([
                            i + 1 + (width + 1) * j,
                            i + 1 + (width + 1) * (j + 1),
                            i + (width + 1) * (j + 1)
                        ]);
                    }
                }
            }
        }
        
        progressStep++;
        // if (typeof CallBack !== 'undefined' && CallBack.SetModelLoadingProgress) {
        //     CallBack.SetModelLoadingProgress(progressStep, totalProgressStep);
        // }
        
        planeModelBuildData.vertices = new Float32Array(points.length * 3);
        const amp = x3pdata.maxZ - x3pdata.minZ;
        let xSum = 0.0;
        let ySum = 0.0;
        let zSum = 0.0;
        // 伪彩色数据
        planeModelBuildData.colorMaps = Array(MapColorType.ColorMax).fill().map(() => new Float32Array(planeModelBuildData.vertices.length));
        let unitStep = 0.0;
        for (let i = 3; i >= -3; i--) {
            const value = Math.abs(amp) * Math.pow(1000.0, i);
            if (value > 1.0 && value < 8000.0) {
                unitStep = Math.pow(1000.0, i);
                break;
            }
        }
        const cz = (x3pdata.maxZ + x3pdata.minZ) / 2.0;
        const xSpace = pointWidth * xincrement;
        planeModelAttribute.unitStep = unitStep;
        planeModelAttribute.cz = cz;
        planeModelAttribute.xSpace = xSpace;
        planeModelAttribute.restoreZ = new Float32Array(points.length);
        planeModelAttribute.rootZ = new Float32Array(points.length);
        for (let i = 0; i < points.length; i++) {
            const point = points[i];
            planeModelBuildData.vertices[i * 3 + 0] = point.x;
            planeModelBuildData.vertices[i * 3 + 1] = point.y;
            let pointZ = 0.0;
            const fraction = (point.z - x3pdata.minZ) / amp;
            pointZ = (point.z - cz) * unitStep / xSpace; //初始读取到的模型Z轴数据过高，需要减小
            
            planeModelAttribute.restoreZ[i] = (point.z - x3pdata.minZ) / absMax;//存储还原之后的值
            planeModelAttribute.rootZ[i] = pointZ;
            //存储伪彩色数据
            MapColor.setColorForZ(planeModelBuildData.colorMaps, fraction, i);
            planeModelBuildData.vertices[i * 3 + 2] = pointZ;
            xSum += point.x;
            ySum += point.y;
            zSum += pointZ;
            
            // 更新最小点和最大点
            planeModelAttribute.keyPoint.minPosition[0] = Math.min(planeModelAttribute.keyPoint.minPosition[0], point.x);
            planeModelAttribute.keyPoint.minPosition[1] = Math.min(planeModelAttribute.keyPoint.minPosition[1], point.y);
            planeModelAttribute.keyPoint.minPosition[2] = Math.min(planeModelAttribute.keyPoint.minPosition[2], pointZ);
            planeModelAttribute.keyPoint.maxPosition[0] = Math.max(planeModelAttribute.keyPoint.maxPosition[0], point.x);
            planeModelAttribute.keyPoint.maxPosition[1] = Math.max(planeModelAttribute.keyPoint.maxPosition[1], point.y);
            planeModelAttribute.keyPoint.maxPosition[2] = Math.max(planeModelAttribute.keyPoint.maxPosition[2], pointZ);
        }
        
        // Progress update
        progressStep++;
        // if (typeof CallBack !== 'undefined' && CallBack.SetModelLoadingProgress) {
        //     CallBack.SetModelLoadingProgress(progressStep, totalProgressStep);
        // }
        
        // 模型包围盒
        planeModelAttribute.keyPoint.modelSize =  glMatrix.vec3.length(
            glMatrix.vec3.subtract(
                glMatrix.vec3.create(),
                planeModelAttribute.keyPoint.maxPosition,
                planeModelAttribute.keyPoint.minPosition
            )
        );
       //获取到平面模型的四个顶点坐标
       planeModelAttribute.keyPoint.topLeft = Algorithm.getVertexCoordinates(planeModelBuildData.vertices, 0);
       planeModelAttribute.keyPoint.topRight = Algorithm.getVertexCoordinates(planeModelBuildData.vertices, pointWidth - 1);
       planeModelAttribute.keyPoint.bottomLeft = Algorithm.getVertexCoordinates(planeModelBuildData.vertices, (pointHeight - 1) * pointWidth);
       planeModelAttribute.keyPoint.bottomRight = Algorithm.getVertexCoordinates(planeModelBuildData.vertices, pointHeight * pointWidth - 1);
        const maxWidth = Math.abs(planeModelAttribute.keyPoint.maxPosition[0] - planeModelAttribute.keyPoint.minPosition[0]);
        const maxHeight = Math.abs(planeModelAttribute.keyPoint.maxPosition[1] - planeModelAttribute.keyPoint.minPosition[1]);
        const maxZHigh = Math.abs(planeModelAttribute.keyPoint.maxPosition[2] - planeModelAttribute.keyPoint.minPosition[2]);
        
        //设置光照半径
        planeModelAttribute.keyPoint.lightRadius = Math.max(
            planeModelAttribute.keyPoint.lightRadius || 0,
            maxWidth,
            maxHeight,
            maxZHigh
        );
        planeModelAttribute.keyPoint.lightRadius = (planeModelAttribute.keyPoint.lightRadius / 2.0) + 2.0;
        
        // 设置模型中心坐标
        planeModelAttribute.keyPoint.centerPosition = glMatrix.vec3.fromValues(
            xSum / points.length,
            ySum / points.length,
            zSum / points.length
        );
        glMatrix.vec3.copy(planeModelAttribute.keyPoint.changeCenterPosition,  planeModelAttribute.keyPoint.centerPosition);
        planeModelBuildData.indices = new Uint32Array(indices.length * 3);
        for (let i = 0; i < indices.length; i++) {
            const indice = indices[i];
            planeModelBuildData.indices[i * 3 + 0] = indice[0];
            planeModelBuildData.indices[i * 3 + 1] = indice[1];
            planeModelBuildData.indices[i * 3 + 2] = indice[2];
        }
        progressStep++;
        // if (typeof CallBack !== 'undefined' && CallBack.SetModelLoadingProgress) {
        //     CallBack.SetModelLoadingProgress(progressStep, totalProgressStep);
        // }
        //更新法线
        planeModelBuildData.normals = new Float32Array(planeModelBuildData.vertices.length);
        Algorithm.updateNormals(planeModelBuildData.vertices, planeModelBuildData.vertices.length, planeModelBuildData.indices, planeModelBuildData.indices.length, planeModelBuildData.normals);
        progressStep++;
        // if (typeof CallBack !== 'undefined' && CallBack.SetModelLoadingProgress) {
        //     CallBack.SetModelLoadingProgress(progressStep, totalProgressStep);
        // }
        return planeModelBuildData;
        

    }
}
