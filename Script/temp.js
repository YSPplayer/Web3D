import {LineModelBuildData,RenderData} from "./Geomety/data.js"
import { Sence } from "./Geomety/sence.js";
import { LineModel } from "./Geomety/linemodel.js";
import { canvas } from "./Util/util.js"
import { GlWindow } from "./Gl/glwindow.js";
function init() {
    //场景
    let sence = new Sence();
    sence.initScene();
    let glwindow = new GlWindow();
    let model = new LineModel();
    let bdata = new LineModelBuildData(); 
    bdata.vertices.push(-0.5);
    bdata.vertices.push(0.0);
    bdata.vertices.push(0.0);
    bdata.vertices.push(0.5);
    bdata.vertices.push(0.0);
    bdata.vertices.push(0.0);
    let success = model.initModel(bdata);
    if(success) {
        console.log('模型初始化成功！');
    } else {
        console.log('模型初始化失败！');
    }
    sence.setCurrentModel(model);
    let data = new RenderData();
    data.width = canvas.width;
    data.height = canvas.height;
    sence.render(data);
}
window.addEventListener('DOMContentLoaded',function(){
   init();
});