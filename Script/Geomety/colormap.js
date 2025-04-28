import { Color } from "./data.js"
export class MapColor {
    constructor(colors = [], indexs = []) {
        this.nbnode = 0;
        this.size = 256;
        // 创建4x256的二维数组
        this.color = Array(4).fill().map(() => Array(this.size).fill(0));
        this.node = Array(this.size).fill(0);
        this.colors = colors;
        this.indexs = indexs;
        if (colors.length > 0 && indexs.length > 0) {
            for (let i = 0; i < this.size; i++) {
                this.color[3][i] = 0;
            }
            this.color[3][0] = 1;
            this.color[3][this.size - 1] = 1;
            this.buildNodes();
            
            for (let index = 0; index < colors.length; ++index) {
                const mcolor = colors[index];
                this.color[0][indexs[index]] = mcolor.r;
                this.color[1][indexs[index]] = mcolor.g;
                this.color[2][indexs[index]] = mcolor.b;
                this.color[3][indexs[index]] = 1;
            }
            this.buildNodes();
            this.build();
        }
    }
    
    buildNodes() {
        this.color[3][0] = 1;
        this.color[3][this.size - 1] = 1;
        this.nbnode = 0;
        for (let i = 0; i < this.size; i++) {
            if (this.color[3][i] === 1) {
                this.node[this.nbnode] = i;
                this.nbnode++;
            }
        }
    }
    
    build() {
        let x1, y1, x2, y2;
        let a, b;
        for (let k = 0; k < 3; k++) {
            for (let i = 0; i < this.nbnode - 1; i++) {
                x1 = this.node[i];
                x2 = this.node[i + 1];
                y1 = this.color[k][x1];
                y2 = this.color[k][x2];
                a = (y2 - y1) / (x2 - x1);
                b = y1 - a * x1;
                for (let j = x1; j < x2; j++) {
                    this.color[k][j] = Math.round(a * j + b);
                }
            }
        }
    }
    
    colorR(index) { return this.color[0][index]; }
    colorG(index) { return this.color[1][index]; }
    colorB(index) { return this.color[2][index]; }
    
    static setColorForZ(colorMaps, fraction, index) {
        // 计算三次方，并将结果缩放到 [0, 255] 范围内
        const scaledValue = Math.pow(fraction, 3) * 255.0;
        // 将结果转换为整数，得到灰度值
        let grey = Math.round(scaledValue);
        let ugrey = 0;
        ugrey = grey > 255 ? 255 : grey;
        ugrey = grey < 0 ? 0 : ugrey;
        // 统一化全部颜色
        for (let i = 0; i < MapColor.mapColors.length; i++) {
            colorMaps[i][index * 3 + 0] = MapColor.mapColors[i].colorR(ugrey) / 255.0;
            colorMaps[i][index * 3 + 1] = MapColor.mapColors[i].colorG(ugrey) / 255.0;
            colorMaps[i][index * 3 + 2] = MapColor.mapColors[i].colorB(ugrey) / 255.0;
        }
    }
}

//伪彩色
MapColor.mapColors = [
    new MapColor(
        [
            new Color(60, 23, 21), new Color(89, 29, 27), new Color(123, 34, 30),
            new Color(200, 122, 39), new Color(243, 203, 75), new Color(246, 245, 191), new Color(253, 253, 253)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 黄铜色
    new MapColor(
        [
            new Color(0, 0, 255), new Color(0, 254, 255), new Color(0, 254, 0),
            new Color(255, 255, 0), new Color(255, 126, 0), new Color(255, 0, 0), new Color(255, 255, 255)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 七彩色
    new MapColor(
        [
            new Color(35, 31, 32), new Color(250, 250, 250), new Color(35, 31, 32),
            new Color(250, 250, 250), new Color(35, 31, 32), new Color(250, 250, 250), new Color(35, 31, 32),
            new Color(250, 250, 250), new Color(35, 31, 32), new Color(250, 250, 250)
        ],
        [25, 50, 75, 100, 125, 150, 175, 200, 225, 255]
    ), // 等高线
    new MapColor(
        [
            new Color(36, 32, 33), new Color(59, 58, 59), new Color(98, 98, 101),
            new Color(138, 140, 143), new Color(182, 183, 186), new Color(221, 222, 224), new Color(250, 250, 250)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 黑白色
    new MapColor(
        [
            new Color(34, 31, 79), new Color(45, 45, 123), new Color(45, 86, 165),
            new Color(48, 149, 210), new Color(134, 210, 221), new Color(220, 241, 244), new Color(250, 250, 250)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 蓝色
    new MapColor(
        [
            new Color(58, 81, 162), new Color(57, 185, 234), new Color(112, 194, 115),
            new Color(119, 191, 65), new Color(218, 225, 68), new Color(243, 137, 43), new Color(237, 47, 39)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 七彩色2
    new MapColor(
        [
            new Color(49, 24, 27), new Color(66, 28, 29), new Color(159, 70, 83),
            new Color(42, 152, 122), new Color(96, 187, 71), new Color(222, 196, 89), new Color(220, 217, 220)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ), // 七彩色3
    new MapColor(
        [
            new Color(98, 94, 169), new Color(89, 107, 157), new Color(55, 136, 162),
            new Color(50, 180, 144), new Color(151, 219, 81), new Color(236, 237, 46), new Color(246, 238, 150)
        ],
        [0, 12, 24, 48, 96, 192, 255]
    ) // 翡翠绿
];