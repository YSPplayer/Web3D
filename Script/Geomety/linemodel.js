import { Model } from "./model.js";
import {VBOType} from "./data.js"
export class LineModel extends Model {
   constructor() {
      super(); 
      this._vbos = Array(VBOType.Vertex + 1).fill(null);
      this._datas = Array(VBOType.Vertex + 1).fill().map(() => []);
   }
   initModel(lineModelBuildData) {
     this._datas[VBOType.Vertex] = [...lineModelBuildData.vertices];
     vertex = this._datas[VBOType.Vertex];
     vsize = vertex.length;
     this._vao = gl.createVertexArray();
     gl.bindVertexArray(vao);
     if (!bindBufferObject(this._vbos[VBOType.Vertex],gl.ARRAY_BUFFER,vertex, vsize,  
        VBOType.Vertex,3,gl.DYNAMIC_DRAW)) return false;
        if(!this._shader.bindShader(v_lineshader,f_lineshader)) return false; 
        this._modelAttribute = lineModelBuildData.modelAttribute.copy();
        this._empty = false;
        return true;
      }
        
      render(data, lightControl, camera) {
         if(this._empty) return;
         gl.enable(gl.LINE_SMOOTH);
         gl.hint(gl.LINE_SMOOTH_HINT, gl.NICEST); 
         gl.enable(gl.BLEND);
         gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
         const lineWidthRange = gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE);
         const lineWidth = Math.min(1.45, lineWidthRange[1]);
         gl.lineWidth(lineWidth);
         if (!this.linkModel) {
            this.shader.setShaderMat4(this.modelAttribute.keyPoint.position, "mposition");
         } else {
            // 使用连接模型的矩阵，提高效率不再计算一次
            this.shader.setShaderMat4(this.linkModel.modelAttribute.keyPoint.position, "mposition");
         }
         
         this.shader.setShaderMat4(cameraAttribute.view, "view");
         this.shader.setShaderMat4(cameraAttribute.projection, "projection");
         this.shader.setShaderVec3(this.modelAttribute.material.diffuse, "defaultObjectColor");
         
         // 绘制线段
         gl.bindVertexArray(this.vao);
         gl.drawArrays(gl.LINES, 0, this.datas[VBOType.Vertex].size / 3); // 每两个顶点为一条线段
         
   }

}