import { Model } from "./model.js";
import { VBOType,v_lineshader,f_lineshader} from "../const.js";
import { PlaneModelAttribute } from "./data.js";
class planemodel extends Model {
    constructor() {
        super(); 
        this._vbos = Array(VBOType.Max).fill(null);
        this._datas = Array(VBOType.Max).fill().map(() => []);
        this._modelAttribute = new PlaneModelAttribute();
    }
    initModel(planeModelBuildData) {
        

    }
}