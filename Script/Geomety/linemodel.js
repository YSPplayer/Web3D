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
         //绑定着色器
         if(!this._shader.bindShader(v_lineshader, f_lineshader)) {
            console.error("着色器绑定失败");
            return false;
         }
         // 处理顶点数据
         this._datas[VBOType.Vertex] = [...lineModelBuildData.vertices];
         let vertex = this._datas[VBOType.Vertex];
         let vsize = vertex.length;
         if (vsize === 0) {
               console.error("顶点数据为空");
               return false;
         }
         // 3. 创建VAO并绑定
         this._vao = gl.createVertexArray();
         gl.bindVertexArray(this._vao);
         // 4. 创建并绑定VBO
         this._vbos[VBOType.Vertex] = Model.bindBufferObject(
               this._vbos[VBOType.Vertex],
               gl.ARRAY_BUFFER,
               vertex, 
               vsize,  
               VBOType.Vertex,
               3,
               gl.STATIC_DRAW
         );
         if (this._vbos[VBOType.Vertex] === null) {
               console.error("绑定缓冲对象失败");
               return false;
         }
         // 复制模型属性
         this._modelAttribute = lineModelBuildData.modelAttribute.copy();
         this._empty = false;
         gl.bindVertexArray(null);
         return true;
      }
        
      render(data, lightControl, camera) {
         if(this._empty) return;
         if(this.linkModel === null) super.updateAttribute(data);
         const shader = this._shader;
         shader.useShader();
         gl.enable(gl.BLEND);
         gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
         const lineWidthRange = gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE);
         const lineWidth = Math.min(1.45, lineWidthRange[1]);
         gl.lineWidth(lineWidth);
         gl.bindVertexArray(this._vao);
         const modelAttribute = this._modelAttribute;
         const cameraAttribute = camera.cameraAttribute;
         if (this.linkModel === null) {
            shader.setShaderMat4(modelAttribute.keyPoint.position, "mposition");
         } else {
            // 使用连接模型的矩阵，提高效率不再计算一次
            shader.setShaderMat4(this.linkModel._modelAttribute.keyPoint.position, "mposition");
         }
         shader.setShaderMat4(cameraAttribute.view, "view");
         shader.setShaderMat4(cameraAttribute.projection, "projection");
           //modelAttribute.material.diffuse
         shader.setShaderVec3([1.0, 1.0, 0.0], "defaultObjectColor");
         gl.bindVertexArray(this._vao);
         gl.drawArrays(gl.LINES, 0, this._datas[VBOType.Vertex].length / 3);
   }

}