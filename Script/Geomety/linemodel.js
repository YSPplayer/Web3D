import { Model } from "./model.js";
import { VBOType,v_lineshader,f_lineshader} from "../const.js";
import { gl } from "../Util/util.js";
export class LineModel extends Model {
   constructor() {
      super(); 
      this._vbos = Array(VBOType.Vertex + 1).fill(null);
      this._datas = Array(VBOType.Vertex + 1).fill().map(() => []);
      this.linkModel = null;
   }
   initModel(lineModelBuildData) {
     this._datas[VBOType.Vertex] = [...lineModelBuildData.vertices];
     let vertex = this._datas[VBOType.Vertex];
     let vsize = vertex.length;
     this._vao = gl.createVertexArray();
     gl.bindVertexArray(this._vao);
     if (!Model.bindBufferObject(this._vbos[VBOType.Vertex],gl.ARRAY_BUFFER,vertex, vsize,  
        VBOType.Vertex,3,gl.DYNAMIC_DRAW)) return false;
        if(!this._shader.bindShader(v_lineshader,f_lineshader)) return false; 
        this._modelAttribute = lineModelBuildData.modelAttribute.copy();
        this._empty = false;
        return true;
      }
        
      render(data, lightControl, camera) {
         if(this._empty) return;
         // gl.enable(gl.LINE_SMOOTH);
         // gl.hint(gl.LINE_SMOOTH_HINT, gl.NICEST); 
         // gl.enable(gl.BLEND);
         // gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
         const lineWidthRange = gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE);
         const lineWidth = Math.min(1.45, lineWidthRange[1]);
         gl.lineWidth(lineWidth);
         const shader = this._shader;
         const modelAttribute = this._modelAttribute;
         const cameraAttribute = camera.cameraAttribute;
         shader.useShader();
         if (this.linkModel === null) {
            shader.setShaderMat4(modelAttribute.keyPoint.position, "mposition");
         } else {
            // 使用连接模型的矩阵，提高效率不再计算一次
            shader.setShaderMat4(this.linkModel._modelAttribute.keyPoint.position, "mposition");
         }
         
         shader.setShaderMat4(cameraAttribute.view, "view");
         shader.setShaderMat4(cameraAttribute.projection, "projection");
         //modelAttribute.material.diffuse
         let as = glMatrix.vec3.create();
         glMatrix.vec3.set(as, 0.0, 0.0, 0.0);
         shader.setShaderVec3(as, "defaultObjectColor");
         
         // 绘制线段
         gl.bindVertexArray(this.vao);
         gl.drawArrays(gl.LINES, 0, this._datas[VBOType.Vertex].size / 3); // 每两个顶点为一条线段
         
   }

}