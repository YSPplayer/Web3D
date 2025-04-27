import { GlType } from "../const.js";
import { X3pData } from "../Geomety/data.js";
String.prototype.arg = function() {
    let str = this;
    for (let i = 0; i < arguments.length; i++) {
        const placeholder = "%" + (i + 1);
        str = str.replace(placeholder, arguments[i]);
    }
    return str;
};
export let canvas = null;
export let gl = null;
export let glType = GlType.Null;
export const Util = {
    async loadX3p(x3pInput) {
        try {
            let zipData;
        
            // 确定输入类型并获取数据
            if (x3pInput instanceof File) {
                // 如果是File对象直接读取
                zipData = await x3pInput.arrayBuffer();
            } else {
                // 如果是URL则使用fetch
                const response = await fetch(x3pInput);
                if (!response.ok) throw new Error('Network response was not ok');
                zipData = await response.arrayBuffer();
            }
            
            // 2. 解压ZIP
            const zip = await JSZip.loadAsync(zipData);
            const xmlFile = zip.file("main.xml");
            if (!xmlFile) throw new Error('Missing main.xml');
            const xmlContent = await xmlFile.async('text');
            
            // 使用DOMParser解析XML
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlContent, "text/xml");
            
            console.log("解析的XML文档:", xmlDoc);
            
            // 处理命名空间问题
            // 查找尺寸元素
            let sizeX = 0;
            let sizeY = 0;
            
            // 尝试多种方式获取尺寸元素，处理可能的命名空间
            // 方法1：直接查询
            const sizeXElement = xmlDoc.querySelector("SizeX");
            const sizeYElement = xmlDoc.querySelector("SizeY");
            
            // 方法2：使用命名空间处理
            if (!sizeXElement || !sizeYElement) {
                // 获取所有MatrixDimension元素
                const matrixDimElements = xmlDoc.getElementsByTagName("MatrixDimension");
                if (matrixDimElements.length > 0) {
                    // 在找到的MatrixDimension下查找SizeX和SizeY
                    for (let i = 0; i < matrixDimElements.length; i++) {
                        const matrixDim = matrixDimElements[i];
                        const xElems = matrixDim.getElementsByTagName("SizeX");
                        const yElems = matrixDim.getElementsByTagName("SizeY");
                        
                        if (xElems.length > 0) sizeX = parseInt(xElems[0].textContent || '0');
                        if (yElems.length > 0) sizeY = parseInt(yElems[0].textContent || '0');
                    }
                }
            } else {
                // 如果直接查询成功
                sizeX = parseInt(sizeXElement.textContent || '0');
                sizeY = parseInt(sizeYElement.textContent || '0');
            }
            
            // 如果尺寸为0，尝试更细致的XML遍历
            if (sizeX === 0 || sizeY === 0) {
                console.log("未找到尺寸元素，尝试遍历所有元素...");
                const allElements = xmlDoc.getElementsByTagName("*");
                for (let i = 0; i < allElements.length; i++) {
                    const elem = allElements[i];
                    if (elem.nodeName.includes("SizeX")) {
                        sizeX = parseInt(elem.textContent || '0');
                    }
                    if (elem.nodeName.includes("SizeY")) {
                        sizeY = parseInt(elem.textContent || '0');
                    }
                }
            }
            
            // 保存找到的尺寸信息
            let x3pdata = new X3pData();
            x3pdata.sizeX = sizeX;
            x3pdata.sizeY = sizeY;
            
            console.log("找到的尺寸:", sizeX, "x", sizeY);
            
            if (sizeX === 0 || sizeY === 0) {
                console.warn("警告: 尺寸为0，可能解析XML失败");
            }
            
            // 初始化坐标轴
            for(let i = 0; i < 3; ++i) {
                x3pdata.axes[i].increment = 1;
            }
            
            // 读取二进制数据
            const binFile = zip.file("bindata/data.bin");
            if (!binFile) throw new Error('Missing binary data file');
            const binArrayBuffer = await binFile.async("arraybuffer");
            const binSize = binArrayBuffer.byteLength;
            
            // 设置点数据大小和初始化Z范围
            x3pdata.pointDataSize = x3pdata.sizeX * x3pdata.sizeY;
            x3pdata.minZ = Number.MAX_VALUE;
            x3pdata.maxZ = -Number.MAX_VALUE;
            
            const numFloats = binSize / 4; 
            // 创建DataView来读取浮点数
            const dataView = new DataView(binArrayBuffer);
            // 创建结果数组
            const pointData = new Float32Array(numFloats);
            
            // 统计有效点数
            let efficientPoints = x3pdata.pointDataSize;
            
            // 处理每个浮点数
            for (let i = 0; i < numFloats; i++) {
                // 读取浮点数（小端字节序）
                const f = dataView.getFloat32(i * 4, true);
                // 乘以1000000（与C++代码相同）
                pointData[i] = f * 1000000.0;
                // 检查是否为NaN并更新统计信息
                if (!isNaN(f)) {
                    if (pointData[i] > x3pdata.maxZ) x3pdata.maxZ = pointData[i];
                    if (pointData[i] < x3pdata.minZ) x3pdata.minZ = pointData[i];
                } else {
                    --efficientPoints;
                }
            }
            
            // 计算有效点百分比  
            x3pdata.efficient = efficientPoints / x3pdata.pointDataSize;
            
            // 处理极端情况
            if (x3pdata.minZ === Number.MAX_VALUE) x3pdata.minZ = 0.0;
            if (x3pdata.maxZ === -Number.MAX_VALUE) x3pdata.maxZ = 0.0;
            
            // 保存点数据
            x3pdata.pointData = pointData;
            
            // 返回处理后的数据
            return x3pdata;
        } catch (error) {
            console.error('Parsing failed:', error);
            throw error;
        }
        
    },
    deleteVertexArray(vao) {
        if (glType === GlType.WebGl2) {
            gl.deleteVertexArray(vao);
        } else if (glType === GlType.WebGl1) {
            const ext = gl.getExtension('OES_vertex_array_object');
            if (ext) {
                ext.deleteVertexArrayOES(vao);
            }
        }
    },
    initializeGL() {
        if(canvas === null && gl === null) {
        canvas = document.getElementById('glwindow');
        //antialias 启用多重采样深度缓冲
        gl = canvas.getContext('webgl2',{ antialias: true,depth: true}) 
         || canvas.getContext('webgl', { antialias: true,depth: true})
         || canvas.getContext('experimental-webgl',
            { antialias: true,depth: true}
        );
        if(gl === null) {
            console.log('浏览器不支持WebGL');
            return;
        }
        if (gl instanceof WebGL2RenderingContext) {
            glType = GlType.WebGl2;
            console.log('当前浏览器使用WebGL2环境');
        } else if (gl instanceof WebGLRenderingContext) {
            glType = GlType.WebGl1;
            console.log('当前浏览器使用WebGL1环境');
        } else {
            glType = GlType.Null;
                console.log('浏览器不支持WebGL');
            }
        }
    }
}
