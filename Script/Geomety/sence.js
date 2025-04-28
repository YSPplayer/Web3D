import { Model } from "./model.js"
import { LineModel } from "./linemodel.js" 
import { Camera } from "./camera.js"
import { LightControl } from "./lightcontrol.js"
import { gl,Util } from "../Util/util.js"
export class Sence {
    constructor() {
        this.currentModel = null;//当前场景中的模型
        this.camera = new Camera(); //相机
        this.lightControl = new LightControl(); //光照

    }

    setCurrentModel(model) {
        if(model.isEmpty()) return false;
        this.currentModel = model;
        this.camera.resetPosition(this.currentModel);
    }

    initScene() {
        Util.initializeGL();
        // 启用深度测试
        gl.enable(gl.DEPTH_TEST);
        // 启用多重采样
        const samples = gl.getParameter(gl.SAMPLES);
        if (samples <= 1) {
            console.warn("多重采样不可用或未启用，尝试使用其他方法提高渲染质量");
        }
    }

    reSetPoisition() {
        if(this.currentModel.isEmpty()) return;
        this.camera.resetPosition(this.currentModel);
        this.currentModel.resetPosition();
    }

    clearScene() {
        if(this.currentModel === null) return;
        this.currentModel.dispose();
        this.currentModel = null;
    }

    render(data) {
        const sceneColor = data.sceneColor;
        gl.viewport(0, 0, data.width, data.height);
        gl.clearColor(sceneColor.redF(), sceneColor.greenF(), 
        sceneColor.blueF(), sceneColor.alphaF());
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.disable(gl.CULL_FACE);
        if(this.currentModel === null || this.currentModel.isEmpty()) return;
        this.camera.render(data);
        this.lightControl.render(data,this.camera);
        this.currentModel.render(data,this.lightControl,this.camera);
    }
}