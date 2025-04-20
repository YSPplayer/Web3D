import { canvas,gl,Util } from "../Util/util.js";
import { GlData } from "../const.js";
import { RenderData } from "../Geomety/data.js";
import { PlaneModelType } from "../const.js";
export class GlWindow {
    constructor() {
        this.data = new RenderData();
        //鼠标按下
        canvas.addEventListener("mousedown",function(event) {
            if (event.button === 0)  { //左键
                GlData.mouseLeftPressed = true;
                GlData.lastX = event.clientX - canvas.getBoundingClientRect().left;
                GlData.lastY = event.clientY - canvas.getBoundingClientRect().top;
            } else if (event.button === 2) { //右键
                GlData.mouseRightPressed = true;
                GlData.lastX = event.clientX - canvas.getBoundingClientRect().left;
                GlData.lastY = event.clientY - canvas.getBoundingClientRect().top;
            }
        });
        //鼠标抬起
        canvas.addEventListener('mouseup', function(event) {
            // 检查是否为左键释放
            if (event.button === 0) {
                GlData.mouseLeftPressed = false;
                GlData.lastX = 0.0;
                GlData.lastY = 0.0;
            }
            // 检查是否为右键释放
            else if (event.button === 2) {
                GlData.mouseRightPressed = false;
                GlData.lastX = 0.0;
                GlData.lastY = 0.0;
            }
        });
        //鼠标移动
        canvas.addEventListener("mousemove", (event) => {
            const rect = canvas.getBoundingClientRect();
            const xpos = event.clientX - rect.left;
            const ypos = event.clientY - rect.top;
            if (GlData.mouseLeftPressed) {
                if (this.data.ptype === PlaneModelType.Ring)  {
                    this.data.oldPos = { x: GlData.lastX, y: GlData.lastY };
                    this.data.newPos = { x: xpos, y: ypos };
                    this.data.ringRotationX = GlData.controlPressed;
                } else {
                    this.rotateXY(this.data.rotationX, this.data.rotationZ, this.data.axisType, xpos, ypos);

                }
                GlData.lastX = xpos;
                GlData.lastY = ypos;
                this.data.rotateXZ = true;
                this.render(); //重新渲染
            }
        });
    }
    render() {

    }
    rotateXY() {
        
    }
}
