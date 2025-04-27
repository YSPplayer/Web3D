import { PlaneModelBuildData,PlaneModelType } from "../Geomety/data.js";
class Algorithm {
    constructor() {

    }
    static BuildPlaneModel(x3pdata) {
        let planeModelBuildData = new PlaneModelBuildData();
        planeModelBuildData.ptype = PlaneModelType.Surface;
        let width = x3pdata.sizeX - 1; //点云数量 - 1
        let height = x3pdata.sizeY - 1; //点云数量 - 1
        

    }
}
