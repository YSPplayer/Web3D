import { Type_AffineTransform, Type_Gamma, stateMachine } from './stateMachine.js'
import { util } from './util.js'

const algargs = {
    contrast:0,//对比度
    brightness:0,//亮度
    gamma:0//伽马亮度
}
const alg = {
   funcMap : new Map(),
   processFunc(color,func,...args) {
        color.r = util.clamp(func(color.r,...args),0,255)
        color.g = util.clamp(func(color.g,...args),0,255)
        color.b = util.clamp(func(color.b,...args),0,255)
        color.a = util.clamp(color.a,0,255)
   },
   processAll(imageData) {
        const { width, height, data } = imageData //data = [r,g,b,a]
        const outData = new Uint8ClampedArray(width * height * 4) //输出像素
        const states = stateMachine.getState()
        for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = (y * width + x) * 4
            const r = data[index]
            const g = data[index + 1]
            const b = data[index + 2]
            const a = data[index + 3]
            const color = {r:r,g:g,b:b,a:a}
            for(let i = 0; i < states.length; ++i) {
                const state = states[i]
                const func = alg.funcMap.get(state)
                if(state === Type_AffineTransform) 
                    alg.processFunc(color,func,algargs.contrast,algargs.brightness)
                else if(state === Type_Gamma)
                    alg.processFunc(color,func,algargs.gamma)
            }
            outData[index] = color.r
            outData[index + 1] = color.g
            outData[index + 2] = color.b
            outData[index + 3] = color.a
        }
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 全部更新当前的状态参数
     * @param {Json} args 
     */
    updateArgs(args) {
        algargs.contrast = args.contrast,
        algargs.brightness = args.brightness,
        algargs.gamma = args.gamma
    },
    /**
     * 获取当前图像的直方图统计数据
     * @param {any} imageData 
     * @returns 
     */
    getHistogramData(imageData) {
       const { width, height, data } = imageData
       const arrayr = new Array(256).fill(0)
       const arrayg = new Array(256).fill(0)
       const arrayb = new Array(256).fill(0)
       const length = width * height * 4
       for (let i = 0; i < length; i += 4) {
            if(data[i + 3] === 0) continue //跳过透明色
            arrayr[data[i]]++
            arrayg[data[i + 1]]++
            arrayb[data[i + 2]]++
        }
        return {
            r:arrayr,
            g:arrayg,
            b:arrayb
        }
    },
    /**
     * 局部直方图均衡化
     * @param {any} imageData 
     */
    limitHistogram(imageData) {
        const { width, height, data } = imageData
        //默认8*8的分组
        const kernelX = 8
        const kernelY = 8
        const tileW = Math.ceil(width / kernelX) //进一位
        const tileH = Math.ceil(height / kernelY)
        const tiles = util.createArray2(kernelY,kernelX)

        for (let ty = 0; ty < kernelY; ty++) {
            for (let tx = 0; tx < kernelX; tx++) {
                const x0 = kernelX * tileW
                const y0 = kernelY * tileH
                const x1 = Math.min(x0 + tileW,width) //边缘整除不足会被包含
                const y1 = Math.min(y0 + tileH,height)
                const tileWidth = x1 - x0
                const tileHeight = y1 - y0
                const tilePixels = tileWidth * tileHeight
                if(tilePixels === 0) continue //数据不存在就跳过
                // 每块自己的 RGBA 数组
                const tileData = new Uint8ClampedArray(tilePixels * 4)
                let ti = 0
                for(let y = y0; y < y1;++y) {
                     for (let x = x0; x < x1; x++) {
                        const index = (y * width + x) * 4
                        tileData[ti++] = data[index]
                        tileData[ti++] = data[index + 1]
                        tileData[ti++] = data[index + 2]
                        tileData[ti++] = data[index + 3]
                     }
                }
                tiles[kernelY][kernelX] = {
                    tx,
                    ty,
                    x0,
                    y0,
                    x1,
                    y1,
                    tileWidth,
                    tileHeight, 
                    imageData : new ImageData(tileData, tileWidth, tileHeight)
                }
            }
        }
        //直方图均衡化
        for (let i = 0; i < kernelY; i++) {
            for (let j = 0; j < kernelX; j++) {
               const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[i][j]
               tiles[i][j].imageData = alg.histogram(imageData)
            }
        }
        //直方图插值
        insertTiles = util.createArray2(kernelY,kernelX)
        for (let iy = 0; iy < kernelY; iy++) {
            for (let ix = 0; ix < kernelX; ix++) {
                const tx_left = ix - 1
                const tx_right = ix + 1
                const ty_up = iy - 1
                const ty_down = iy + 1
                const fx_left = 0
                const fx_right = 0
                const fy_up = 0
                const fy_down = 0
                const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[iy][ix]
                if(tx_left >= 0) { //当前点的左侧区域块
                    const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[iy][tx_left]
                    fx_left = (x0 + x1) / 2
                }  
                if(tx_right < kernelX) {//当前点的右侧区域块
                    const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[iy][tx_right]
                    fx_right = (x0 + x1) / 2
                }
                if(ty_up >= 0) {//当前点的上方区域块
                    const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[ty_up][ix]
                    fy_up = (y0 + y1) / 2
                }
                if(ty_down < kernelY) {//当前点的下方区域块
                    const {tx,ty,x0,y0,x1,y1,tileWidth,tileHeight,imageData} = tiles[ty_up][ix]
                    fy_down = (y0 + y1) / 2
                }
                for(let y = y0; y < y1;++y) {
                    for (let x = x0; x < x1; x++) {
                        const index = (y * width + x) * 4
                        index = 
                    }
                }
                
            }
        }
    },
    /**
     * 全局直方图均衡化
     * @param {any} imageData 
     * @returns 
     */
    histogram(imageData) {
        const { width, height, data } = imageData //data = [r,g,b,a]
        const { r: histR, g: histG, b: histB } = alg.getHistogramData(imageData)
        const outData = new Uint8ClampedArray(width * height * 4) //输出像素
        //计算CDF统一查表
        const mapR = new Uint8Array(256)
        const mapG = new Uint8Array(256)
        const mapB = new Uint8Array(256)
        const total = width * height
        let cdfR = 0, cdfG = 0, cdfB = 0
        for(let i = 0; i < 256; ++i) {
             //计算求和
             cdfR += histR[i]
             cdfG += histG[i]
             cdfB += histB[i]
             //CDF统一查表
             mapR[i] = util.clamp(Math.round(cdfR / total * 255),0,255)
             mapG[i] = util.clamp(Math.round(cdfG / total * 255),0,255)
             mapB[i] = util.clamp(Math.round(cdfB / total * 255),0,255)
             
        }
        const length = total * 4
        //直接赋值
        for (let i = 0; i < length; i += 4) {
            outData[i] = mapR[data[i]] 
            outData[i + 1] = mapG[data[i + 1]] 
            outData[i + 2] = mapB[data[i + 2]] 
            outData[i + 3] = data[i + 3] 
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 更新当前的图像渲染
     */
    render(imageData) {
        return alg.processAll(imageData)
    },
    /**
     * 修改图像的亮度/对比度
     * @param {number} value 
     * @param {number} contrast 
     * @param {number} brightness 
     * @returns 
     */
    affineTransform(value,contrast,brightness) {
        return util.clamp(contrast * (value - 128) + 128 + brightness,0,255)
    },
    /**
     * 修改图像的伽马亮度
     * @param {number} value 
     * @param {number} gamma 
     * @returns 
     */
    gamma(value,gamma) {
        value = Math.pow(value / 255.0, gamma) * 255.0
        return util.clamp(value,0,255)
    }
}
alg.funcMap = new Map(
    [
        [Type_AffineTransform, alg.affineTransform],
        [Type_Gamma, alg.gamma],
    ]
)

export { alg }
