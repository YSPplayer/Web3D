import {LineModelBuildData,RenderData,PlaneModelBuildData,PlaneModelAttribute,ModelKeyPoint,X3pData} from "./Geomety/data.js"
import { Sence } from "./Geomety/sence.js"
import { LineModel } from "./Geomety/linemodel.js"
import { Algorithm } from "./Math/algorithm.js"
import { Planemodel } from "./Geomety/planemodel.js"
import { canvas } from "./Util/util.js"
import { GlWindow } from "./Gl/glwindow.js"
function init() {
    //场景
    let glwindow = new GlWindow();
    glwindow.initGL();
    
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
    x3pdata.sizeX = 30;
    x3pdata.sizeY = 20;
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

window.addEventListener('DOMContentLoaded',function(){
//     const canvas = document.getElementById('glwindow'); // 假设HTML中有一个id为glCanvas的canvas元素
// const gl = canvas.getContext('webgl2');
init();
// if (gl === null) {
//     console.error('无法初始化WebGL，您的浏览器不支持WebGL2');
//     return;
//   }
  
//   // 设置清空颜色并清空画布
//   gl.clearColor(0.8, 0.8, 0.8, 1.0);
//   gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  
//   // 创建顶点着色器
//   const vertexShaderSource = `#version 300 es
//   in vec4 aPosition;
//   void main() {
//     gl_Position = aPosition;
//   }`;
  
//   // 创建片段着色器
//   const fragmentShaderSource = `#version 300 es
//   precision mediump float;
//   out vec4 fragColor;
//   void main() {
//     fragColor = vec4(1.0, 0.0, 0.0, 1.0); // 红色
//   }`;
  
//   // 编译着色器函数
//   function compileShader(gl, type, source) {
//     const shader = gl.createShader(type);
//     gl.shaderSource(shader, source);
//     gl.compileShader(shader);
    
//     if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
//       console.error('着色器编译错误:', gl.getShaderInfoLog(shader));
//       gl.deleteShader(shader);
//       return null;
//     }
    
//     return shader;
//   }
  
//   // 编译顶点着色器和片段着色器
//   const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
//   const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
  
//   // 创建并链接着色器程序
//   const program = gl.createProgram();
//   gl.attachShader(program, vertexShader);
//   gl.attachShader(program, fragmentShader);
//   gl.linkProgram(program);
  
//   if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
//     console.error('程序链接错误:', gl.getProgramInfoLog(program));
//     return;
//   }
  
//   // 使用着色器程序
//   gl.useProgram(program);
  
//   // 创建顶点数据 - 一个正方形 (-0.5, -0.5) 到 (0.5, 0.5)
//   const vertices = new Float32Array([
//     -0.5, -0.5, 0.0,  // 左下角
//      0.5, -0.5, 0.0,  // 右下角
//      0.5,  0.5, 0.0,  // 右上角
//     -0.5,  0.5, 0.0   // 左上角
//   ]);
  
//   // 创建索引数据 - 两个三角形组成一个正方形
//   const indices = new Uint16Array([
//     0, 1, 2,  // 第一个三角形
//     0, 2, 3   // 第二个三角形
//   ]);
  
//   // 创建顶点数组对象(VAO)
//   const vao = gl.createVertexArray();
//   gl.bindVertexArray(vao);
  
//   // 创建并绑定顶点缓冲
//   const vertexBuffer = gl.createBuffer();
//   gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
//   gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
  
//   // 启用顶点属性
//   const positionLocation = gl.getAttribLocation(program, 'aPosition');
//   gl.enableVertexAttribArray(positionLocation);
//   gl.vertexAttribPointer(positionLocation, 3, gl.FLOAT, false, 0, 0);
  
//   // 创建并绑定索引缓冲
//   const indexBuffer = gl.createBuffer();
//   gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
//   gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
  
//   // 检查WebGL错误
//   let error = gl.getError();
//   if (error !== gl.NO_ERROR) {
//     console.error('WebGL错误:', error);
//   }
  
//   // 绘制正方形
//   gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_SHORT, 0);
  
//   // 再次检查WebGL错误
//   error = gl.getError();
//   if (error !== gl.NO_ERROR) {
//     console.error('绘制后WebGL错误:', error);
//   } else {
//     console.log('正方形绘制成功');
//   }
  
//   // 清理
//   gl.bindVertexArray(null);
});