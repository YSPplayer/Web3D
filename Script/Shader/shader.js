//Shader脚本管理类
export class Shader {
    constructor() {
        this.shaderProgram = null; 
    }

    useShader() {
        gl.useProgram(this.shaderProgram);
    }

    dispose() {
        if(this.shaderProgram !== null) 
            gl.deleteProgram(this.shaderProgram);
    }

    /*
        创建编译shader文件
    */
    bindShader(vertexShaderSource, fragmentShaderSource) {
        this.shaderProgram = gl.createProgram();
        const vShader = this.createShader(gl.VERTEX_SHADER, vertexShaderSource); // 创建顶点着色器
        const fShader = this.createShader(gl.FRAGMENT_SHADER, fragmentShaderSource); // 创建片段着色器
        if (vShader !== null && fShader !== null) {
            gl.attachShader(this.shaderProgram, vShader);
            gl.attachShader(this.shaderProgram, fShader);
            gl.linkProgram(this.shaderProgram);
            gl.validateProgram(this.shaderProgram);
            gl.deleteShader(vShader);
            gl.deleteShader(fShader);
            const success = gl.getProgramParameter(this.shaderProgram, gl.LINK_STATUS);
            if (!success) {
                const infoLog = gl.getProgramInfoLog(this.shaderProgram);
                console.error("shader绑定失败:", infoLog);
                return false;
            }
            return true;
        }
        return false;
    }

    setShaderMat4(mat4, key) {
        gl.uniformMatrix4fv(gl.getUniformLocation(this.shaderProgram, key), false, mat4);
    }

    setShaderMat3(mat3, key) {
        gl.uniformMatrix3fv(gl.getUniformLocation(this.shaderProgram, key), false, mat3);
    }

    setShaderVec3(vec3, key) {
        gl.uniform3fv(gl.getUniformLocation(this.shaderProgram, key), vec3);
    }

    setShaderFloat(value, key) {
        gl.uniform1f(gl.getUniformLocation(this.shaderProgram, key), value);
    }

    setShaderInt(value, key) {
        gl.uniform1i(gl.getUniformLocation(this.shaderProgram, key), value);
    }

    setShaderBoolean(value, key) {
        gl.uniform1i(gl.getUniformLocation(this.shaderProgram, key), value ? 1 : 0);
    }

    createShader(type, source) {
        const shader = gl.createShader(type); 
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        const success = gl.getShaderParameter(shader, gl.COMPILE_STATUS);
        if (!success) {
            const infoLog = gl.getShaderInfoLog(shader);
            console.error("shader编译失败:", infoLog);
            return null;
        }
        return shader;
    }
}
