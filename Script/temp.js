import {LineModelBuildData} from "./Geomety/data.js"
function init() {
    Util.initializeGL();
    const sdata = new LineModelBuildData();
    const centerPos = sdata.modelAttribute.keyPoint.centerPosition;
    console.log(`centerPosition: [${centerPos[0]}, ${centerPos[1]}, ${centerPos[2]}]`);
    // 检查 WebGL 是否可用
    if (!gl) {
        console.error('无法初始化 WebGL。您的浏览器可能不支持它。');
    }
    // 定义三角形的顶点
    const vertices = new Float32Array([
        0.0,  0.5,   // 顶点 A
    -0.5, -0.5,   // 顶点 B
        0.5, -0.5    // 顶点 C
    ]);
    // 创建缓冲区并将顶点数据传入
    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    // 定义顶点着色器
    const vertexShaderSource = `
        attribute vec2 coordinates;
        void main(void) {
            gl_Position = vec4(coordinates, 0.0, 1.0);
        }
    `;

    // 定义片段着色器
    const fragmentShaderSource = `
        void main(void) {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); // 红色
        }
    `;

    // 创建着色器
    function createShader(gl, source, type) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('着色器编译错误：', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    // 创建程序
    const vertexShader = createShader(gl, vertexShaderSource, gl.VERTEX_SHADER);
    const fragmentShader = createShader(gl, fragmentShaderSource, gl.FRAGMENT_SHADER);
    const shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);
    gl.useProgram(shaderProgram);

    // 绑定缓冲区并绘制三角形
    const coord = gl.getAttribLocation(shaderProgram, 'coordinates');
    gl.vertexAttribPointer(coord, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(coord);
    gl.clearColor(0.0, 0.0, 0.0, 1.0); // 清空颜色为黑色
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
}
window.addEventListener('DOMContentLoaded',function(){
   init();
});