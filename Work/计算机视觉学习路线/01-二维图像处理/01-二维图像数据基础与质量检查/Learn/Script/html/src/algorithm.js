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
     * 直方图均衡化
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
