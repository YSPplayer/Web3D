import { LightAttribute } from "./data.js";
export class LightControl {
    constructor() {
        this.lightAttribute = new LightAttribute();
    }
    render(data, camera) {
        const color = data.lightColor;
        const material = this.lightAttribute.material;
        glMatrix.vec3.set(
            material.diffuse,
            color.redF() * data.lightDiffuse,
            color.greenF() * data.lightDiffuse,
            color.blueF() * data.lightDiffuse
        );
        
        // 设置环境光颜色 (环境光 = 漫反射 * 环境光强度)
        glMatrix.vec3.scale(material.ambient, material.diffuse, data.lightAmbient);
        
        // 设置镜面反射颜色
        glMatrix.vec3.set(
            material.specular,
            1.0 * data.lightIntensity,
            1.0 * data.lightIntensity,
            1.0 * data.lightIntensity
        );
        
        // 更新光源位置
        if (data.moveXLight === 0.0 && data.moveYLight === 0.0) {
            // 默认位置
            glMatrix.vec3.set(this.lightAttribute.position, 0.0, 0.0, 3.0);
        } else {
            // 计算移动距离和比例
            const xyLength = Math.sqrt(Math.pow(data.moveXLight, 2) + Math.pow(data.moveYLight, 2));
            const xyLengthRatio = Math.min(xyLength, 1.0);
            
            // 设置光源位置
            glMatrix.vec3.set(
                this.lightAttribute.position,
                xyLengthRatio * this.lightAttribute.lightRadius * data.moveXLight / xyLength,
                xyLengthRatio * this.lightAttribute.lightRadius * data.moveYLight / xyLength,
                data.zDynamic
            );
        }
    }
}

