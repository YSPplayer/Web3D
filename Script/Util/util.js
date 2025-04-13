String.prototype.arg = function() {
    let str = this;
    for (let i = 0; i < arguments.length; i++) {
        const placeholder = "%" + (i + 1);
        str = str.replace(placeholder, arguments[i]);
    }
    return str;
};
const GlType = Object.freeze({
    Null: 0,  
    WebGl: 1,
    WebGl2:2
});
let canvas = null;
let gl = null;
let glType = GlType.Null;
const Util = {
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
        gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if(gl === null) {
            console.log('浏览器不支持WebGL');
            return;
        }
        if (gl instanceof WebGL2RenderingContext) {
            glType = GlType.WebGl2;
        } else if (gl instanceof WebGLRenderingContext) {
            glType = GlType.WebGl1;
        } else {
            glType = GlType.Null;
                console.log('浏览器不支持WebGL');
            }
        }
    }
}
