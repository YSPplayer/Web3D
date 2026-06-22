export class Model {
    constructor(points,indexs) {
        this.points = points;
        this.indexs = indexs;
        this.color = '#abc1a3ff';
        this.move = {x: 0, y: 0, z: 0}; //移动角
        this.angle = {x: 0, y: 0, z: 0}; //旋转角
        const sumx = points.reduce((sum, point) => sum + point.x, 0);
        const sumy = points.reduce((sum, point) => sum + point.y, 0);
        const sumz = points.reduce((sum, point) => sum + point.z, 0);
        this.center = {
            x: sumx / points.length,
            y: sumy / points.length,
            z: sumz / points.length
        }
    }
    //透视投影映射公式,转为透视视口
    perspectiveProject(x,y,z,d = 1) { 
        /*
            x' = x / z * d
            y' = y / z * d
        */
        const x_ = x / z;
        const y_ = y / z;
        return {
            x: x_ * d,
            y: y_ * d
        }
    }
    //模型平移
    transform(points,move) {
        points.forEach(point => {
            point.x += move.x;
            point.y += move.y;
            point.z += move.z;
        })
    }
    rotateX(points,angle) {
        if(angle === 0) return
        points.forEach(point => {
            const y = point.y;
            const z = point.z;
            point.y = this.center.y + (y - this.center.y) * Math.cos(angle) - (z - this.center.z) * Math.sin(angle);
            point.z = this.center.z + (y - this.center.y) * Math.sin(angle) + (z - this.center.z) * Math.cos(angle);
        })
    }
    rotateY(points,angle) {
        if(angle === 0) return
        points.forEach(point => {
            const x = point.x;
            const z = point.z;
            point.x = this.center.x + (x - this.center.x) * Math.cos(angle) + (z - this.center.z) * Math.sin(angle);
            point.z = this.center.z - (x - this.center.x) * Math.sin(angle) + (z - this.center.z) * Math.cos(angle);
        })
    }
    rotateZ(points,angle) {
        if(angle === 0) return
        points.forEach(point => {
            const x = point.x;
            const y = point.y;
            point.x = this.center.x + (x - this.center.x) * Math.cos(angle) - (y - this.center.y) * Math.sin(angle);
            point.y = this.center.y + (x - this.center.x) * Math.sin(angle) + (y - this.center.y) * Math.cos(angle);
        })
    }
    render(canvas,move,angle) {
        const ctx = canvas.getContext('2d');
        if(!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height); //先清空画布
        ctx.fillStyle = this.color;
        ctx.beginPath();
        const points = structuredClone(this.points);
        //旋转
        this.rotateY(points, angle.y);
        this.rotateX(points, angle.x);
        this.rotateZ(points, angle.z);
        //平移
        this.transform(points, move);
        const point0 = this.perspectiveProject(points[this.indexs[0]].x, points[this.indexs[0]].y, points[this.indexs[0]].z);
        ctx.moveTo(point0.x, point0.y);
        for(let i = 1; i < this.indexs.length; i++) {
            const point = this.perspectiveProject(points[this.indexs[i]].x, points[this.indexs[i]].y, points[this.indexs[i]].z);
            ctx.lineTo(point.x, point.y);
        }
        ctx.closePath();
        ctx.fill();
    }
}