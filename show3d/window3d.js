import { Model } from "./model.js";
export class MoveData {
    constructor() {
        this.startX = 0;//X移动位置
        this.startY = 0;//Y移动位置
        this.lastX = 0;//上次移动位置
        this.lastY = 0;//上次移动位置
        this.isDragging = false;//是否正在拖动
        this.totalDeltaX  = 0;//累计偏移量
        this.totalDeltaY  = 0;//累计偏移量
        this.currentDeltaX  = 0;//当前增量
        this.currentDeltaY  = 0;//当前增量
    }
}
export class Window3d {
    constructor(canvas, width, height) {
        this.canvas = canvas
        this.canvas.width = width
        this.canvas.height = height
        this.models = []
        this.moveLeft = new MoveData(); //左侧偏移
        this.moveRight = new MoveData(); //右侧偏移
        this.boundMouseDown = this.handleMouseDown.bind(this);
        this.boundMouseMove = this.handleMouseMove.bind(this);
        this.boundMouseUp = this.handleMouseUp.bind(this);
        canvas.addEventListener('mousedown', this.boundMouseDown);
    }
    addModel(model) {
        this.models.push(model);
    }
    drawModel() {
        this.models.forEach(element => {
            element.render(this.canvas,{x:this.moveLeft.totalDeltaX,y:this.moveLeft.totalDeltaY, z: 0});
        });
    }
    render() {
        this.drawModel();    
    }

    handleMouseDown(event) {
        if(event.button === 0) {
            const moveLeft = this.moveLeft;
            moveLeft.isDragging = true;
            moveLeft.startX = event.clientX;
            moveLeft.startY = event.clientY;
            moveLeft.lastX = event.clientX;
            moveLeft.lastY = event.clientY;
            moveLeft.currentDeltaX = 0;
            moveLeft.currentDeltaY = 0;
            document.addEventListener('mousemove', this.boundMouseMove);
            document.addEventListener('mouseup', this.boundMouseUp);
        }
    }
    
    handleMouseMove(event) {
        if(event.button === 0 && this.moveLeft.isDragging) {
            const moveLeft = this.moveLeft;
            moveLeft.currentDeltaX = event.clientX - moveLeft.lastX;
            moveLeft.currentDeltaY = event.clientY - moveLeft.lastY;
            moveLeft.totalDeltaX = moveLeft.totalDeltaX + moveLeft.currentDeltaX;
            moveLeft.totalDeltaY = moveLeft.totalDeltaY + moveLeft.currentDeltaY;
            moveLeft.lastX = event.clientX;
            moveLeft.lastY = event.clientY;
            this.render()
        }
    }
    
    handleMouseUp(event) {
        if(event.button === 0 && this.moveLeft.isDragging) {
            const moveLeft = this.moveLeft;
            moveLeft.isDragging = false;
            moveLeft.startX = 0;
            moveLeft.startY = 0;
            moveLeft.lastX = 0;
            moveLeft.lastY = 0;
            moveLeft.currentDeltaX = 0;
            moveLeft.currentDeltaY = 0;
            document.removeEventListener('mousemove', this.boundMouseMove);
            document.removeEventListener('mouseup', this.boundMouseUp);
        }
    }

}