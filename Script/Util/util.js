import { GlType } from "../const.js";
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
