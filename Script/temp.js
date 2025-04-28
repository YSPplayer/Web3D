import {LineModelBuildData,RenderData,PlaneModelBuildData,PlaneModelAttribute,ModelKeyPoint,X3pData} from "./Geomety/data.js"
import { Sence } from "./Geomety/sence.js"
import { LineModel } from "./Geomety/linemodel.js"
import { Algorithm } from "./Math/algorithm.js"
import { Planemodel } from "./Geomety/planemodel.js"
import { Util,canvas,gl } from "./Util/util.js"
import { GlWindow } from "./Gl/glwindow.js"
function init() {
    //场景
    let glwindow = new GlWindow();
    glwindow.initGL();
    createPlaneModel(glwindow);
    return;
    // 首先让我们创建和显示一个简单的线段模型，确认渲染管线是正常的
    let lineModel = new LineModel();
    let lineData = new LineModelBuildData(); 
    lineData.vertices.push(-0.5);
    lineData.vertices.push(0.0);
    lineData.vertices.push(0.0);
    lineData.vertices.push(0.5);
    lineData.vertices.push(0.0);
    lineData.vertices.push(0.0);
    let lineSuccess = lineModel.initModel(lineData);
    if(lineSuccess) {
        console.log('线段模型初始化成功！');
        glwindow.setCurrentModel(lineModel);
        glwindow.render(); // 渲染线段模型
        
        // 等待1秒后切换到平面模型
        setTimeout(() => {
            console.log('正在切换到平面模型...');
            createPlaneModel(glwindow);
        }, 1000);
    } else {
        console.log('线段模型初始化失败！');
    }
}

function createPlaneModel(glwindow) {
    let x3pdata = new X3pData();
    x3pdata.maxZ = 0;
    x3pdata.minZ = 0;
    x3pdata.sizeX = 3000;
    x3pdata.sizeY = 500;
    for(let i = 0; i < 3; ++i) {
        x3pdata.axes[i].increment = 1;

    }
    x3pdata.pointData =  new Array(x3pdata.sizeX * x3pdata.sizeY).fill(null);
    for(let i = 0; i < x3pdata.sizeX * x3pdata.sizeY; i++) {
        x3pdata.pointData[i] = 0.5;
    }
    let bdata = Algorithm.BuildPlaneModel(x3pdata);
    let model = new Planemodel();
    // 初始化模型
    let success = model.initModel(bdata);
    if(success) {
        console.log('平面模型初始化成功！');
        glwindow.setCurrentModel(model);
        glwindow.render(); // 立即渲染
    } else {
        console.log('平面模型初始化失败！');
    }
}
function resizeCanvas() {
    canvas.width = window.innerWidth - 100;
    canvas.height = window.innerHeight - 100;
}
function setupHiDPICanvas() {
    const pixelRatio = window.devicePixelRatio || 1; //css像素对应多少物理像素
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * pixelRatio;
    canvas.height = rect.height * pixelRatio;
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
window.addEventListener('DOMContentLoaded',function(){
    //init();
    let glwindow = new GlWindow();
    glwindow.initGL();
    setupHiDPICanvas();
    glwindow.render();
    const selectButton = document.getElementById('selectX3pButton');
    const fileInput = document.getElementById('x3pFileInput');
    selectButton.addEventListener('click', function() {
        fileInput.click();
    });
    fileInput.addEventListener('change', async function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // 检查文件扩展名
        if (!file.name.toLowerCase().endsWith('.x3p')) {
            alert('请选择.x3p格式的文件!');
            return;
        }
        
        try {
            // 显示加载状态
            //infoDisplay.textContent = '正在加载X3P文件...';
            
            // 调用loadX3p函数处理文件
            console.log(file);
            glwindow.clearScene();
            const x3pdata = await Util.loadX3p(file);
            let bdata = Algorithm.BuildPlaneModel(x3pdata);
            let model = new Planemodel();
            // 初始化模型
            let success = model.initModel(bdata);
            if(success) {
                console.log('平面模型初始化成功！');
                glwindow.setCurrentModel(model);
                glwindow.render(); // 立即渲染
            } else {
                console.log('平面模型初始化失败！');
            }
            // // 显示结果
            // infoDisplay.innerHTML = `
            //     <h3>X3P文件信息</h3>
            //     <p>尺寸: ${x3pData.sizeX} x ${x3pData.sizeY} x ${x3pData.sizeZ}</p>
            //     <p>MD5: ${x3pData.md5}</p>
            // `;
            
        } catch (error) {
            //infoDisplay.textContent = `加载失败: ${error.message}`;
            console.error('X3P处理错误:', error);
        }
    });
});