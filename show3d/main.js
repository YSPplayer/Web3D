import {Window3d} from "./window3d.js";
import {Model} from "./model.js";
window.onload = function() {
    const canvas  = document.getElementById('show3d');
    const window3d = new Window3d(canvas, 1000, 700);
    const model = new Model([
        {x: 100, y: 200, z: 1},
        {x: 200, y: 200, z: 1},
        {x: 100, y: 400, z: 1},
        {x: 200, y: 400, z: 1}
    ],[
        0, 1, 3, 2
    ]);
    window3d.addModel(model);
    window3d.render();
}