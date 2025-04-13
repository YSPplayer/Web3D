import {CameraAttribute,} from "./data.js"
class Camera {
    constructor() {
        this.cameraAttribute = new CameraAttribute();
        // 创建投影矩阵
        this.par_fov = glMatrix.mat4.create(); // 平行视口
        this.per_fov = glMatrix.mat4.create(); // 透视视口
        // 设置相机位置和朝向
        glMatrix.vec3.set(this.cameraAttribute.position, 0.0, 0.0, 3.0);
        glMatrix.vec3.set(this.cameraAttribute.front, 0.0, 0.0, -1.0);
        glMatrix.vec3.set(this.cameraAttribute.worldUp, 0.0, 1.0, 0.0);
        this.cameraAttribute.right = glMatrix.vec3.create();
        glMatrix.vec3.cross(this.cameraAttribute.right, this.cameraAttribute.front, this.cameraAttribute.worldUp);
        glMatrix.vec3.normalize(this.cameraAttribute.right, this.cameraAttribute.right);
        this.cameraAttribute.up = glMatrix.vec3.create();
        glMatrix.vec3.cross(this.cameraAttribute.up, this.cameraAttribute.right, this.cameraAttribute.front);
        glMatrix.vec3.normalize(this.cameraAttribute.up, this.cameraAttribute.up);
        this.cameraAttribute.view = glMatrix.mat4.create();
        const target = glMatrix.vec3.create();
        glMatrix.vec3.add(target, this.cameraAttribute.position, this.cameraAttribute.front);
        glMatrix.mat4.lookAt(
            this.cameraAttribute.view,
            this.cameraAttribute.position,
            target,
            this.cameraAttribute.up
        );
        this.cameraAttribute.projection = glMatrix.mat4.create();
        glMatrix.mat4.copy(this.par_fov, this.cameraAttribute.projection);
        glMatrix.mat4.copy(this.per_fov, this.cameraAttribute.projection);
    }
    
    getProjection(isParallelFov) {
        return isParallelFov ? this.par_fov : this.per_fov;
    }

    render(data) {
        //平行视口
        glMatrix.mat4.ortho(
            this.par_fov,
            -data.parallel,
            data.parallel,
            -data.parallel * data.height / data.width,
            data.parallel * data.height / data.width,
            0.01,
            10.0
        );

        //透视视口  
        glMatrix.mat4.perspective(
            this.per_fov,
            data.fov, 
            data.width / data.height,
            0.1,
            3000.0
        );
        if (data.isParallelFov) {
            glMatrix.mat4.copy(this.cameraAttribute.projection, this.par_fov);
        } else {
            glMatrix.mat4.copy(this.cameraAttribute.projection, this.per_fov);
        }
    }

    getNDC(pos) {
        const vtransform = this.cameraAttribute.view;
        const ptransform = this.cameraAttribute.projection;
        const p = glMatrix.vec4.fromValues(pos[0], pos[1], pos[2], 1.0);
        const clipSpaceP = glMatrix.vec4.create();
        glMatrix.vec4.transformMat4(clipSpaceP, p, vtransform);  
        glMatrix.vec4.transformMat4(clipSpaceP, clipSpaceP, ptransform); 
        return vec2.fromValues(
            clipSpaceP[0] / clipSpaceP[3],
            clipSpaceP[1] / clipSpaceP[3]
        );
    }

    resetPosition(model) {
        const modelAttribute = model.modelAttribute;
        glMatrix.vec3.set(
            this.cameraAttribute.position,
            0.0,
            0.0,
            3.0 * modelAttribute.keyPoint.modelSize
        );
        glMatrix.vec3.set(this.cameraAttribute.up, 0.0, 1.0, 0.0);
        const direction = glMatrix.vec3.create();
        glMatrix.vec3.subtract(direction, modelAttribute.keyPoint.centerPosition, this.cameraAttribute.position);
        glMatrix.vec3.normalize(this.cameraAttribute.front, direction);
        glMatrix.vec3.cross(this.cameraAttribute.right, this.cameraAttribute.front, this.cameraAttribute.up);
        glMatrix.vec3.normalize(this.cameraAttribute.right, this.cameraAttribute.right);
        glMatrix.vec3.cross(this.cameraAttribute.up, this.cameraAttribute.right, this.cameraAttribute.front);
        glMatrix.vec3.normalize(this.cameraAttribute.up, this.cameraAttribute.up);
        const target = glMatrix.vec3.create();
        glMatrix.vec3.add(target, this.cameraAttribute.position, this.cameraAttribute.front);
        glMatrix.mat4.lookAt(
            this.cameraAttribute.view,
            this.cameraAttribute.position,
            target,
            this.cameraAttribute.up
        );
    }
}

