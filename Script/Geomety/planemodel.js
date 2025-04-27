import { Model } from "./model.js";
import { VBOType,ImageType,v_lineshader,f_lineshader,PlaneModelType} from "../const.js";
import { PlaneModelAttribute } from "./data.js";
import { gl } from "../Util/util.js";
export class Planemodel extends Model {
    constructor() {
        super(); 
        this._vbos = Array(VBOType.Max).fill(null); //VBO
        this.ebo = null; //EBO
        this.indices = [];//EBO数据
        this.textures = Array(ImageType.Max).fill(null); //Texture
        this._datas = Array(VBOType.Max).fill().map(() => []);//模型数据
        this._modelAttribute = new PlaneModelAttribute();//模型属性
        this.ptype = PlaneModelType.Surface;//模型类型
    }
    initModel(planeModelBuildData) {
        if(!this._shader.bindShader(v_lineshader, f_lineshader)) {
            console.error("[Planemodel.initModel]着色器绑定失败");
            return false;
        }
        //this.colormaps
        this.ptype = planeModelBuildData.ptype;
        this._modelAttribute = planeModelBuildData.planeModelAttribute;
        this._datas[VBOType.Vertex] = planeModelBuildData.vertices;
        this._datas[VBOType.Texture] = planeModelBuildData.textures;
        this._datas[VBOType.Normal] = planeModelBuildData.normals;
        this._datas[VBOType.Wall] = planeModelBuildData.walls;
        this._datas[VBOType.Flag] = planeModelBuildData.flags;
        this._datas[VBOType.Index] = planeModelBuildData.index;
        this.indices = planeModelBuildData.indices;
        const vsize =  this._datas[VBOType.Vertex].length;
        const isize = this.indices.length;
        const tsize = this._datas[VBOType.Texture].length;
        const nsize = this._datas[VBOType.Normal].length;
        const wsize = this._datas[VBOType.Wall].length;
        const fsize = this._datas[VBOType.Flag].length;
        const indexsize = this._datas[VBOType.Index].length;
        this.hasTexture = planeModelBuildData.hasTexture;
        this._vao = gl.createVertexArray();
        gl.bindVertexArray(this._vao);
        if((this._vbos[VBOType.Vertex] = Model.bindBufferObject(
            this._vbos[VBOType.Vertex],
            gl.ARRAY_BUFFER,
            this._datas[VBOType.Vertex], 
            vsize,  
            VBOType.Vertex,
            3,
            gl.DYNAMIC_DRAW‌
        )) === null || (this.ebo = Model.bindBufferObject(
                    this.ebo,
                    gl.ELEMENT_ARRAY_BUFFER,
                    this.indices,
                    isize,
                    -1,
                    -1
                )) === null ) {
            console.error("[Planemodel.initModel]绑定缓冲对象失败");
            return false;
        }
        this._empty = false;
        gl.bindVertexArray(null);
        console.log("[Planemodel.initModel]平面模型创建成功.");
        return true;
    }

    render(data, lightControl, camera) {
        if(this._empty) return;
        super.updateAttribute(data);//更新模型属性
        //绑定贴图
        // for (let i = 0; i < this.textures.length; i++) {
        //     gl.activeTexture(gl.TEXTURE0 + i);
        //     // 绑定纹理到当前激活的纹理单元
        //     gl.bindTexture(gl.TEXTURE_2D, this.textures[i]);
        // }
        const shader = this._shader;
        shader.useShader();
        gl.bindVertexArray(this._vao);
        const modelAttribute = this._modelAttribute;
        const cameraAttribute = camera.cameraAttribute;
        shader.setShaderMat4(modelAttribute.keyPoint.position, "mposition");
        shader.setShaderMat4(cameraAttribute.view, "view");
        shader.setShaderMat4(cameraAttribute.projection, "projection");
        //modelAttribute.material.diffuse
        shader.setShaderVec3([1.0, 1.0, 0.0], "defaultObjectColor");
        gl.drawElements(gl.TRIANGLES, this.indices.length, gl.UNSIGNED_INT, 0);
         // 再次检查WebGL错误
        let error = gl.getError();
        if (error !== gl.NO_ERROR) {
            console.error('绘制后WebGL错误:', error);
        } else {
            console.log('正方形绘制成功');
        }
  
    }
}
