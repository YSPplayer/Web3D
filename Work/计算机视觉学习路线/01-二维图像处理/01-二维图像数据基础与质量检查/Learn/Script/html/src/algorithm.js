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
        //最多8 * 8 防止图像宽度小于8
        const tilesX = Math.min(8, width)
        const tilesY = Math.min(8, height)
        // 每个元素保存当前区域的 R、G、B 三张 LUT，创建初始的局部直方图存储数组
        const tileLuts = Array.from(
            { length: tilesY },
            () => new Array(tilesX)
        )
        /*
            统计每一个区域的直方图，并生成对应的LUT
        */
       for(let ty = 0; ty < tilesY; ty ++) {
            //获取到当前的Y方向起始位置
            const y0 =  Math.floor(ty * (height / tilesY))
            //获取当前的Y方向结尾位置
            const y1 = Math.floor((ty + 1) * (height / tilesY))
            for (let tx = 0; tx < tilesX; tx++) {
                //获取到当前的X方向起始位置
                const x0 = Math.floor(tx * (width / tilesX))
                //获取到当前的X方向结尾位置
                const x1 = Math.floor((tx + 1) * (width / tilesX))
                const histR = new Uint32Array(256)
                const histG = new Uint32Array(256)
                const histB = new Uint32Array(256)
                //获取到像素数量
                let pixelCount = 0
                for(let y = y0; y < y1; y++) {
                    for(let x = x0; x < x1; x++) {
                        const index = (y * width + x) * 4
                        const alpha = data[index + 3]
                        //不让透明背景影响直方图
                        if(alpha === 0) continue
                        histR[data[index]]++
                        histG[data[index + 1]]++
                        histB[data[index + 2]]++
                        pixelCount++
                    }
                }
                //设置当前空间块的局部全局直方图
                tileLuts[ty][tx] = {
                    r: util.createEqualizeLut(histR, pixelCount),
                    g: util.createEqualizeLut(histG, pixelCount),
                    b: util.createEqualizeLut(histB, pixelCount)
                }
            }

       }
       const outData = new Uint8ClampedArray(data.length)
       /*
        阶段二，进行线性插值
       */
       for(let y = 0; y < height; y++) {
          //把图像坐标转为相对于当前点像素的中心块的坐标，方便计算权重
          const gridY = ((y + 0.5) * tilesY / height) - 0.5
          let ty0
          let ty1
          let fy
          if (gridY <= 0) {
            ty0 = 0
            ty1 = 0
            fy = 0
          } else if (gridY >= tilesY - 1) {
            ty0 = tilesY - 1
            ty1 = tilesY - 1
            fy = 0
          } else {
            ty0 = Math.floor(gridY)
            ty1 = ty0 + 1
            fy = gridY - ty0
          }
          for (let x = 0; x < width; x++) {
            const index = (y * width + x) * 4
            const alpha = data[index + 3]
            //透明像素保持不变
            if (alpha === 0) { //先初始化输出像素中的值
                outData[index] = data[index]
                outData[index + 1] = data[index + 1]
                outData[index + 2] = data[index + 2]
                outData[index + 3] = alpha
                continue
            }
            //X方向映射坐标
            const gridX = ((x + 0.5) * tilesX / width) - 0.5    
            let tx0
            let tx1
            let fx
            //获取到fy和fx
            if (gridX <= 0) {
                tx0 = 0
                tx1 = 0
                fx = 0
            } else if (gridX >= tilesX - 1) {
                tx0 = tilesX - 1
                tx1 = tilesX - 1
                fx = 0
            } else {
                tx0 = Math.floor(gridX)
                tx1 = tx0 + 1
                fx = gridX - tx0
            }
            //获取到上下左右四个部分的lut查询表
            const lut00 = tileLuts[ty0][tx0]
            const lut10 = tileLuts[ty0][tx1]
            const lut01 = tileLuts[ty1][tx0]
            const lut11 = tileLuts[ty1][tx1]
            //获取到要查询表的对象索引
            const r = data[index]
            const g = data[index + 1]
            const b = data[index + 2]
            //双线性插值
            outData[index] = util.bilinear(
                lut00.r[r],
                lut10.r[r],
                lut01.r[r],
                lut11.r[r],
                fx,
                fy
            )
            outData[index + 1] = util.bilinear(
                lut00.g[g],
                lut10.g[g],
                lut01.g[g],
                lut11.g[g],
                fx,
                fy
            )
            outData[index + 2] = util.bilinear(
                lut00.b[b],
                lut10.b[b],
                lut01.b[b],
                lut11.b[b],
                fx,
                fy
            )
            outData[index + 3] = alpha
          }
       }
       return new ImageData(outData, width, height)
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
