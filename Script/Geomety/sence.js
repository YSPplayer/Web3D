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
    }

    reSetPoisition() {
        if(this.currentModel.isEmpty()) return;
        this.camera.resetPosition(this.currentModel);
        this.currentModel.resetPosition();
    }

    clearScene() {
        this.currentModel.dispose();
    }

    render(data) {
        const sceneColor = data.sceneColor;
        gl.clearColor(sceneColor.redF(), sceneColor.greenF(), 
        sceneColor.blueF(), sceneColor.alphaF());
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.disable(gl.CULL_FACE);
        if(this.currentModel.isEmpty()) return;
        this.camera.render(data);
        this.lightControl.render(data,this.camera);
        this.currentModel.render(data,this.lightControl,this.camera);
    }
}