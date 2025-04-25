import { canvas,gl,Util } from "../Util/util.js";
import { GlData } from "../const.js";
import { RenderData } from "../Geomety/data.js";
import { PlaneModelType } from "../const.js";
import { Sence } from "../Geomety/sence.js";
export class GlWindow {
    constructor() {
        this.data = new RenderData();
        this.sence = new Sence();
        //处理上下文丢失
        // canvas.addEventListener('webglcontextlost', function(event) {
        //     event.preventDefault();
        //     // 处理上下文丢失
        // }, false);
        
        // canvas.addEventListener('webglcontextrestored', function() {
        //     // 重新初始化WebGL状态和资源
        // }, false);
        
    }
    initGL() {
        this.sence.initScene();
        document.addEventListener('keydown',function(event) {
            if(event.key === 'Control') {
                GlData.controlPressed = true;
            }
         });
         document.addEventListener('keyup',function(event) {
            if(event.key === 'Control' ) {
                GlData.controlPressed = false;
            }
         });
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
                    const {rotationX,rotationZ}  = this.rotateXY(this.data.rotationX, this.data.rotationZ, xpos, ypos);
                    this.data.rotationX = rotationX;
                    this.data.rotationZ = rotationZ;
                }
                GlData.lastX = xpos;
                GlData.lastY = ypos;
                this.data.rotateXZ = true;
                this.render(); 
            } else if (GlData.mouseRightPressed) {
                const offsetX = (xpos - GlData.lastX) / 1000.0 * (this.data.fov / this.data.baseFov);
                const offsetY = (GlData.lastY - ypos) / 1000.0 * (this.data.fov / this.data.baseFov);
                const {moveX,moveY}  = this.moveXY(this.data.moveX,this.data.moveY,offsetX,offsetY);
                this.data.moveX = moveX;
                this.data.moveY = moveY;
                GlData.lastX = xpos;
                GlData.lastY = ypos;
                this.data.moveXY = true;
                this.render();
            }
        });
        //放大缩小
        canvas.addEventListener('wheel', (event) => {
            event.preventDefault();
            // 获取滚轮delta值（正值表示向上滚动，负值表示向下滚动）
            const delta = event.deltaY * -1;
            if(GlData.controlPressed){

            } else {
                if(this.data.isParallelFov){ //平行视口
                    delta > 0 ?   this.data.parallel /= 1.3 : this.data.parallel *= 1.3;
                } else {
                    const step = delta / 60.0 * Math.PI / (6 * 180.0);
                    this.data.fov-= step;
                    this.data.fov = Math.max(this.data.minFov, Math.min(this.data.fov, this.data.maxFov));
                }
            }
            this.render();
        });
        //阻止默认事件
        canvas.addEventListener('contextmenu', function(event) {
            event.preventDefault();
            return false;
        }, false);
    }
    setCurrentModel(model) {
        this.sence.setCurrentModel(model);
    }
    render() {
        this.data.width = canvas.width;
        this.data.height = canvas.height;
        this.sence.render(this.data);
        this.resetAttribute();
    }
    resetClearScene() {
        this.resetAttribute();
        this.reSetPoisitionAttribute();
    }
    resetAttribute() {
        this.data.rotateXZ = false;
        this.data.ringRotationX = false;
        this.data.moveXY = false;
        this.data.adjustLight = false;
    }
    reSetPoisitionAttribute() {
        GlData.lastX = 0.0;
        GlData.lastY = 0.0;
        this.data.fov = this.data.baseFov;
        this.data.parallel = this.data.baseParallel;
        this.data.moveX = 0.0;
        this.data.moveY = 0.0;
        this.data.rotationX = 0.0;
        this.data.rotationZ = 0.0;
        this.data.oldPos = { x: -99.0, y: -99.0 };
        this.data.newPos = { x: -99.0, y: -99.0 };
    }
    moveXY(moveX,moveY,offsetX,offsetY) {
        moveX += offsetX;
        moveY += offsetY;
        return {moveX:moveX,moveY:moveY};
    }
    rotateXY(rotationX,rotationZ,xpos, ypos) {
      //  const modelType = this.scene.getPlaneModelType();
      if (!GlData.controlPressed) {
        rotationZ += ((xpos - GlData.lastX) * (GlData.modelSensitivity) / 3.0);
        let incrementZ;
        let axle = 0;
        if (rotationZ > 0.0) {
            incrementZ = Math.floor(rotationZ) % 360;
        } else {
            incrementZ = (Math.floor(rotationZ) % 360) + 360.0; // 对负角度进行处理
        }
        if (incrementZ > 90.0 && incrementZ <= 180.0) axle = 1;
        else if (incrementZ > 180.0 && incrementZ <= 270.0) axle = 2;
        else if (incrementZ > 270.0 && incrementZ <= 360.0) axle = 3;
        else axle = 0;
        if (rotationX > 0 && rotationX < 90)  axle = (axle + 2) % 4;
      
      }
      GlData.lastX = xpos;
      const incrementX = ((ypos - GlData.lastY) * (GlData.modelSensitivity) / 3.0);
      if (rotationX + incrementX >= -90.0 && rotationX + incrementX <= 90.0) {
          rotationX += (ypos - GlData.lastY) / 3.0;
          GlData.lastY = ypos;
      }
      return {rotationX:rotationX,rotationZ:rotationZ};
    }
}
