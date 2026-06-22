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
    perspectiveProject(x,y,z, d = 800, cameraDistance = 800) { 
        /*
            x' = x / z * d
            y' = y / z * d
        */
        const viewZ = z + cameraDistance;
        const scale = d / viewZ;
        return {
            x: x * scale,
            y: y * scale
        };
    }
    //模型平移
    transform(points,move) {
        points.forEach(point => {
            point.x += move.x;
            point.y += move.y;
            point.z += move.z;
        })
    }
    //模型旋转
    rotateEuler(point,angle) {
        const cx = this.center.x;
        const cy = this.center.y;
        const cz = this.center.z;
        //世界坐标转模型的局部坐标，把模型的世界坐标转为相当于模型中心点的局部坐标
        let x = point.x - cx;
        let y = point.y - cy;
        let z = point.z - cz;
        const cosX = Math.cos(angle.x);
        const sinX = Math.sin(angle.x);
        const cosY = Math.cos(angle.y);
        const sinY = Math.sin(angle.y);
        const cosZ = Math.cos(angle.z);
        const sinZ = Math.sin(angle.z);
        // 1. rotate Z
        const x1 = x * cosZ - y * sinZ;
        const y1 = x * sinZ + y * cosZ;
        const z1 = z;
        // 2. rotate Y
        const x2 = x1 * cosY + z1 * sinY;
        const y2 = y1;
        const z2 = -x1 * sinY + z1 * cosY;
        // 3. rotate X
        const x3 = x2;
        const y3 = y2 * cosX - z2 * sinX;
        const z3 = y2 * sinX + z2 * cosX;
        return {
            x: x3 + cx,
            y: y3 + cy,
            z: z3 + cz
        };
    }
    render(canvas,move,angle) {
        const ctx = canvas.getContext('2d');
        if(!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height); //先清空画布
        ctx.fillStyle = this.color;
        ctx.beginPath();
        let points = structuredClone(this.points);
        //旋转
        points = this.points.map(point => this.rotateEuler(point, angle));
        // //平移
        // this.transform(points, move);
        const point0 = this.perspectiveProject(points[this.indexs[0]].x, points[this.indexs[0]].y, points[this.indexs[0]].z);
        //平移
        ctx.moveTo(point0.x + move.x, point0.y + move.y);
        for(let i = 1; i < this.indexs.length; i++) {
            const point = this.perspectiveProject(points[this.indexs[i]].x, points[this.indexs[i]].y, points[this.indexs[i]].z);
            ctx.lineTo(point.x + move.x, point.y + move.y);
        }
        ctx.closePath();
        ctx.fill();
    }
}