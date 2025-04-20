import { Shader } from "../Shader/shader.js";
import { gl,Util } from "../Util/util.js";
import { ModelAttribute } from "./data.js";
import { PlaneModelType } from "../const.js";
export class Model {
    constructor() {
        this._modelAttribute = new ModelAttribute(); // 模型属性
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
    updateAttribute(data) {
        if (!data.rotateXZ && !data.moveXY) return;
        // 获取旋转和移动参数
        const rotationZ = data.rotationZ;
        const rotationX = data.rotationX;
        const moveX = data.moveX;
        const moveY = data.moveY;
        // 获取模型关键点
        const keyPoint = this._modelAttribute.keyPoint;
        const position = keyPoint.position;
        const centerPosition = keyPoint.centerPosition;
        const changeCenterPosition = keyPoint.changeCenterPosition;
        if(data.ptype === PlaneModelType.Surface){
            // 创建变换矩阵 - 先平移到中心点
            const changeTranslationToCenter = glMatrix.mat4.create();
            glMatrix.mat4.translate(changeTranslationToCenter, glMatrix.mat4.create(), changeCenterPosition);
            // 绕X轴旋转
            glMatrix.mat4.rotate(
                changeTranslationToCenter, 
                changeTranslationToCenter, 
                glMatrix.glMatrix.toRadian(rotationX), 
                [1.0, 0.0, 0.0]
            );
            // 绕Z轴旋转
            glMatrix.mat4.rotate(
                changeTranslationToCenter, 
                changeTranslationToCenter, 
                glMatrix.glMatrix.toRadian(rotationZ), 
                [0.0, 0.0, 1.0]
            );
            // 平移回原位置
            const translationBack = glMatrix.mat4.create();
            glMatrix.mat4.translate(
                translationBack, 
                glMatrix.mat4.create(), 
                [-changeCenterPosition[0], -changeCenterPosition[1], 0.0]
            );
            // 计算组合变换
            glMatrix.mat4.multiply(position, changeTranslationToCenter, translationBack);
            // Y轴平移
            const translateY = glMatrix.mat4.create();
            glMatrix.mat4.translate(translateY, glMatrix.mat4.create(), [0.0, moveY, 0.0]);
            glMatrix.mat4.multiply(position, position, translateY);
            // X轴平移
            const translateX = glMatrix.mat4.create();
            glMatrix.mat4.translate(translateX, glMatrix.mat4.create(), [moveX, 0.0, 0.0]);
            glMatrix.mat4.multiply(position, position, translateX);
            // 更新变化中心点
            const tempVec4 = glMatrix.vec4.fromValues(
                centerPosition[0], centerPosition[1], centerPosition[2], 1.0
            );
            const tempResult = glMatrix.vec4.create();
            // 组合变换应用到中心点
            glMatrix.mat4.multiply(translateY, translateX, translateY);
            glMatrix.vec4.transformMat4(tempResult, tempVec4, translateY);
            // 更新changeCenterPosition
            glMatrix.vec3.set(
                changeCenterPosition, 
                tempResult[0], 
                tempResult[1], 
                tempResult[2]
            );
        } else {
        if (data.rotateXZ) {
                // 验证位置数据有效性
                if (data.oldPos.x === -99.0 && data.oldPos.y === -99.0 && 
                    data.newPos.x === -99.0 && data.newPos.y === -99.0) return;
                const hitOld = ProjectOnSphere(data.oldPos, data.width, data.height);
                const hitNew = ProjectOnSphere(data.newPos, data.width, data.height);
                const rotationSpeed = 2.0; 
                const dotProduct = glMatrix.vec3.dot(hitOld, hitNew);
                const clampedDot = Math.max(-1.0, Math.min(1.0, dotProduct));
                const rotationAngle = Math.acos(clampedDot) * rotationSpeed;
                const rotationAxis = glMatrix.vec3.create();
                glMatrix.vec3.cross(rotationAxis, hitOld, hitNew);
                glMatrix.vec3.normalize(rotationAxis, rotationAxis); 
                // 环形旋转处理
                if (data.ringRotationX) {
                    const yDiff = data.newPos.y - data.oldPos.y;
                    const currentRotationMat = glMatrix.mat4.create();
                    glMatrix.mat4.fromQuat(currentRotationMat, data.currentRotation);
                    const localXAxis = glMatrix.vec3.fromValues(
                        currentRotationMat[0], 
                        currentRotationMat[4], 
                        currentRotationMat[8]
                    );
                    glMatrix.vec3.normalize(localXAxis, localXAxis);
                    const modifiedRotationSpeed = 1.5;
                    glMatrix.vec3.copy(rotationAxis, localXAxis);
                    rotationAngle = yDiff * 0.01 * modifiedRotationSpeed;
                }
                if (glMatrix.vec3.length(rotationAxis) < 0.001) return;
                const newRotation = glMatrix.quat.create();
                glMatrix.quat.setAxisAngle(newRotation, rotationAxis, rotationAngle);
                if (isNaN(data.currentRotation[0])) {
                    glMatrix.quat.identity(data.currentRotation);
                }
                glMatrix.quat.multiply(
                    data.currentRotation, 
                    newRotation, 
                    data.currentRotation
                );
            }
            const transform = glMatrix.mat4.create();
            glMatrix.mat4.translate(transform, transform, changeCenterPosition);
            const rotationMat = glMatrix.mat4.create();
            glMatrix.mat4.fromQuat(rotationMat, data.currentRotation);
            glMatrix.mat4.multiply(transform, transform, rotationMat);
            const translationBack = glMatrix.mat4.create();
            glMatrix.mat4.translate(
                translationBack, 
                glMatrix.mat4.create(), 
                [-changeCenterPosition[0], -changeCenterPosition[1], 0.0]
            );
            glMatrix.mat4.multiply(position, transform, translationBack);
            const translateY = glMatrix.mat4.create();
            glMatrix.mat4.translate(translateY, glMatrix.mat4.create(), [0.0, moveY, 0.0]);
            glMatrix.mat4.multiply(position, position, translateY);
            const translateX = glMatrix.mat4.create();
            glMatrix.mat4.translate(translateX, glMatrix.mat4.create(), [moveX, 0.0, 0.0]);
            glMatrix.mat4.multiply(position, position, translateX);
            const tempVec4 = glMatrix.vec4.fromValues(
                centerPosition[0], centerPosition[1], centerPosition[2], 1.0
            );
            const tempResult = glMatrix.vec4.create();
            glMatrix.mat4.multiply(translateY, translateX, translateY);
            glMatrix.vec4.transformMat4(tempResult, tempVec4, translateY);
            glMatrix.vec3.set(
                changeCenterPosition, 
                tempResult[0], 
                tempResult[1], 
                tempResult[2]
            );

        }
    }

    // 绑定缓冲对象
    static bindBufferObject(oID, bufferType, data, dataSize, attributeIndex, componentsPerVertex, usage = gl.STATIC_DRAW) {
        let buffer = oID;
        const empty = buffer === null;
        // 生成并绑定 VBO
        if (empty) {
            buffer = gl.createBuffer();
        }
        // 设置当前 VBO 上下文
        gl.bindBuffer(bufferType, buffer);
        // 先绑定空指针，避免显存溢出的问题
        if (empty) {
            gl.bufferData(bufferType, dataSize * Float32Array.BYTES_PER_ELEMENT, usage);
        }
        // 持久映射 CPU 缓冲区到 GPU 数据指针
        // if (data !== null) {
        //     const buffer = gl.mapBufferRange(bufferType, 0, dataSize * Float32Array.BYTES_PER_ELEMENT, gl.MAP_WRITE_BIT);
        //     if (!buffer) {
        //         console.error("绑定缓冲对象错误：GPU映射失败！");
        //         return false; // 检查映射是否成功
        //     }
        //     // 复制数据到缓冲区
        //     new Float32Array(buffer).set(data);
        //     gl.unmapBuffer(bufferType); // 取消映射
        // }
         // 直接使用bufferData传输数据
        if (data !== null) {
            // 创建Float32Array视图，确保数据格式正确
            const typedArray = (data instanceof Float32Array) ? data : new Float32Array(data);
            // 使用bufferData直接传输数据到GPU
            gl.bufferData(bufferType, typedArray, usage);
        } 
        if (bufferType === gl.ARRAY_BUFFER) {
            gl.vertexAttribPointer(attributeIndex, componentsPerVertex, gl.FLOAT, false, componentsPerVertex * Float32Array.BYTES_PER_ELEMENT, 0);
            gl.enableVertexAttribArray(attributeIndex); // 启用顶点属性
        }
        const error = gl.getError();
        if (error !== gl.NO_ERROR) {
            console.error("WebGL错误：", error);
            return null;
        }
        return buffer;
    }
}
