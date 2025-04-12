import { Model } from "./model.js";
import {LineModelBuildData,VBOType,ModelAttribute} from "./data.js"
import { Shader } from "../Shader/shader.js";
class LineModel extends Model {
   constructor() {
      super(); // 调用父类构造函数
      this._vbos = Array(VBOType.Vertex + 1).fill(null);
      this._datas = Array(VBOType.Vertex + 1).fill().map(() => []);
      this._modelAttribute = new ModelAttribute();
   }
   initModel(lineModelBuildData) {
     this._datas[VBOType.Vertex] = [...lineModelBuildData.vertices];
     vertex = this._datas[VBOType.Vertex];
     vsize = vertex.length;
     this._vao = gl.createVertexArray();
     gl.bindVertexArray(vao);
     if (!bindBufferObject(this._vbos[VBOType.Vertex],gl.ARRAY_BUFFER,vertex, vsize,  
        VBOType.Vertex,3,gl.DYNAMIC_DRAW)) return false;
   }
   // bool InitModel(const LineModelBuildData& build, Model* linkModel = nullptr);
}

export { LineModel };