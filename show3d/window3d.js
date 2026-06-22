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
        this.sensitivity = 0.005
        this.moveLeft = new MoveData(); //左侧偏移
        this.moveRight = new MoveData(); //右侧偏移
        this.boundMouseDown = this.handleMouseDown.bind(this);
        this.boundMouseMove = this.handleMouseMove.bind(this);
        this.boundMouseUp = this.handleMouseUp.bind(this);
        this.boundContextMenu = this.handleContextMenu.bind(this);
        canvas.addEventListener('mousedown', this.boundMouseDown);
        canvas.addEventListener('contextmenu', this.boundContextMenu);
    }
    addModel(model) {
        this.models.push(model);
    }
    drawModel() {
        let rotationz = this.moveRight.totalDeltaX % 360
        let rotationx = this.moveRight.totalDeltaY % 360
        if (rotationz < 0) rotationz += 360;
        if (rotationx < 0) rotationx += 360;
        rotationz = rotationz * Math.PI / 180;
        rotationx = rotationx * Math.PI / 180;
        this.models.forEach(element => {
            element.render(this.canvas,{x:this.moveLeft.totalDeltaX,y:this.moveLeft.totalDeltaY, z: 0}, {x: rotationx, y: 0, z: rotationz});
        });
    }
    render() {
        this.drawModel();    
    }
    handleContextMenu(event) {
         event.preventDefault()
    }
    handleMouseDown(event) {
        if(event.button === 0) { //平移
            const moveLeft = this.moveLeft;
            this.moveRight.isDragging = false;
            moveLeft.isDragging = true;
            moveLeft.startX = event.clientX;
            moveLeft.startY = event.clientY;
            moveLeft.lastX = event.clientX;
            moveLeft.lastY = event.clientY;
            moveLeft.currentDeltaX = 0;
            moveLeft.currentDeltaY = 0;
            document.addEventListener('mousemove', this.boundMouseMove);
            document.addEventListener('mouseup', this.boundMouseUp);
        } else if(event.button === 2) { //旋转
            const moveRight = this.moveRight;
            this.moveLeft.isDragging = false;
            moveRight.isDragging = true;
            moveRight.startX = event.clientX;
            moveRight.startY = event.clientY;
            moveRight.lastX = event.clientX;//Z方向旋转
            moveRight.lastY = event.clientY;//X方向旋转
            moveRight.currentDeltaX = 0;
            moveRight.currentDeltaY = 0;
            document.addEventListener('mousemove', this.boundMouseMove);
            document.addEventListener('mouseup', this.boundMouseUp);
        }
    }
    
    handleMouseMove(event) {
        if(this.moveLeft.isDragging) {
            const moveLeft = this.moveLeft;
            moveLeft.currentDeltaX = event.clientX - moveLeft.lastX;
            moveLeft.currentDeltaY = event.clientY - moveLeft.lastY;
            moveLeft.totalDeltaX = moveLeft.totalDeltaX + moveLeft.currentDeltaX;
            moveLeft.totalDeltaY = moveLeft.totalDeltaY + moveLeft.currentDeltaY;
            moveLeft.lastX = event.clientX;
            moveLeft.lastY = event.clientY;
            this.render()
        } else if(this.moveRight.isDragging) {
            const moveRight = this.moveRight;
            moveRight.currentDeltaX = event.clientX - moveRight.lastX;
            moveRight.currentDeltaY = event.clientY - moveRight.lastY;
            moveRight.totalDeltaX = moveRight.totalDeltaX + moveRight.currentDeltaX * this.sensitivity;
            moveRight.totalDeltaY = moveRight.totalDeltaY + moveRight.currentDeltaY * this.sensitivity;
            moveRight.lastX = event.clientX;
            moveRight.lastY = event.clientY;
            this.render()
        }
    }
    
    handleMouseUp(event) {
        if(this.moveLeft.isDragging) {
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
        } else if(this.moveRight.isDragging) {
            const moveRight = this.moveRight;
            moveRight.isDragging = false;
            moveRight.startX = 0;
            moveRight.startY = 0;
            moveRight.lastX = 0;
            moveRight.lastY = 0;
            moveRight.currentDeltaX = 0;
            moveRight.currentDeltaY = 0;
            document.removeEventListener('mousemove', this.boundMouseMove);
            document.removeEventListener('mouseup', this.boundMouseUp);
        }
    }

}