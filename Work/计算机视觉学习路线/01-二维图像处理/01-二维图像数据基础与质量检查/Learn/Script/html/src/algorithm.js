import { Type_AffineTransform, Type_Gamma, stateMachine } from './stateMachine.js'
import { util } from './util.js'

const algargs = {
    contrast:0,//对比度
    brightness:0,//亮度
    gamma:0//伽马亮度
}
const channelOffsets = { r: 0, g: 1, b: 2 }
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
    getHistogramData(imageData, channel = null) {
        if (channel !== null) {
            return { [channel]: alg.getChannelStatistics(imageData, channel).histogram }
        }
        const result = {
            r: new Array(256).fill(0),
            g: new Array(256).fill(0),
            b: new Array(256).fill(0)
        }
        const { data } = imageData
        for (let i = 0; i < data.length; i += 4) {
            if (data[i + 3] === 0) continue
            result.r[data[i]]++
            result.g[data[i + 1]]++
            result.b[data[i + 2]]++
        }
        return result
    },
    /**
     * 单次遍历统计一个通道的直方图和像素范围
     * @param {ImageData} imageData
     * @param {'r'|'g'|'b'} channel
     */
    getChannelStatistics(imageData, channel) {
        const offset = channelOffsets[channel]
        if (offset === undefined) throw new RangeError(`Unsupported channel: ${channel}`)
        const histogram = new Array(256).fill(0)
        const { data } = imageData
        let min = 255
        let max = 0
        let pixelCount = 0
        for (let i = 0; i < data.length; i += 4) {
            if (data[i + 3] === 0) continue
            const value = data[i + offset]
            histogram[value]++
            min = Math.min(min, value)
            max = Math.max(max, value)
            pixelCount++
        }
        return {
            histogram,
            min: pixelCount === 0 ? 0 : min,
            max: pixelCount === 0 ? 0 : max
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
     * 正态分布噪音
     * @param {any} imageData 
     */
    gaussianNoise(imageData, seed = Date.now()) {
        const { width, height, data } = imageData
        const length = width * height * 4
        const outData = new Uint8ClampedArray(length) //输出像素
        const random = util.createSeededRandom(seed)
        for (let i = 0; i < length; i += 4) {
            outData[i] = data[i] + util.gaussianRandom(0, 1, random)
            outData[i + 1] = data[i + 1] + util.gaussianRandom(0, 1, random)
            outData[i + 2] = data[i + 2] + util.gaussianRandom(0, 1, random)
            outData[i + 3] = data[i + 3] 
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 椒盐分布噪音
     * @param {any} imageData 
     */
    saltPepperNoise(imageData, seed = Date.now()) {
        const { width, height, data } = imageData
        const length = width * height * 4
        const p = 0.05 //约5%的像素受到污染
        const outData = new Uint8ClampedArray(length) //输出像素
        const random = util.createSeededRandom(seed)
        for (let i = 0; i < length; i += 4) {
            const r = random() //生成0-1之间的随机数
            if(r <  p / 2) { //2.5%的概率变成胡椒
                outData[i] = outData[i + 1] = outData[i + 2] = 0
            } else if(r <  p ) { //2.5%的概率变成盐
                outData[i] = outData[i + 1] = outData[i + 2] = 255
            } else {
                outData[i] = data[i]
                outData[i + 1] = data[i + 1]
                outData[i + 2] = data[i + 2]
            }
            outData[i + 3] = data[i + 3]
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 散斑噪音
     * @param {any} imageData 
     * @returns 
     */
    speckleNoise(imageData, seed = Date.now()) {
        const { width, height, data } = imageData
        const length = width * height * 4
        const outData = new Uint8ClampedArray(length)
        const random = util.createSeededRandom(seed)
        for (let i = 0; i < length; i += 4) {
            const noise = 1 + util.gaussianRandom(0, 0.1, random)
            outData[i]     = data[i] * noise
            outData[i + 1] = data[i + 1] * noise
            outData[i + 2] = data[i + 2] * noise
            outData[i + 3] = data[i + 3]
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 构建高斯滤波核
     * @param {number} kernelSize 
     * @param {number} sigma 
     */
    createGaussianKernel(kernelSize, sigma) {
        const kernel = new Float32Array(kernelSize * kernelSize)
        const center = Math.floor(kernelSize / 2)
        let sum = 0
        for (let y = 0; y < kernelSize; y++) {
            for (let x = 0; x < kernelSize; x++) {
                const dx = x - center
                const dy = y - center
                const value = Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
                kernel[y * kernelSize + x] = value
                sum += value
            }
        }
        // 归一化
        for (let i = 0; i < kernel.length; i++) {
            kernel[i] /= sum
        }
        return kernel
    },
    /**
     * 构建均值滤波核
     * @param {number} kernelSize 
     */
    createMeanKernel(kernelSize) {
        const length = kernelSize * kernelSize
        return new Float32Array(length).fill(1 / length)
    },
    
    /**
     * 通用滤波函数
     * @param {any} imageData 
     * @param {number} kernelSize 
     */
    commonFilter(imageData,kernel,kernelSize) {
        const { width, height, data } = imageData
        const outData = new Uint8ClampedArray(width * height * 4)
        const half = Math.floor(kernelSize / 2)
        for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
                let sumR = 0, sumG = 0, sumB = 0
                let weightSum = 0//实际使用的权重之和
                for (let ky = -half; ky <= half; ky++) {
                    for (let kx = -half; kx <= half; kx++) {
                        const ny = y + ky
                        const nx = x + kx
                        if (ny >= 0 && ny < height && nx >= 0 && nx < width) {
                            const idx = (ny * width + nx) * 4
                            const w = kernel[(ky + half) * kernelSize + (kx + half)]
                            //权重相乘
                            sumR += data[idx] * w
                            sumG += data[idx + 1] * w
                            sumB += data[idx + 2] * w
                            weightSum += w
                        }
                    }
                }
                const index = (y * width + x) * 4
                outData[index]     = Math.round(sumR / weightSum)
                outData[index + 1] = Math.round(sumG / weightSum)
                outData[index + 2] = Math.round(sumB / weightSum)
                outData[index + 3] = data[index + 3]
            }
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 均值滤波
     * @param {any} imageData 
     * @param {number} kernelSize 
     */
    meanFilter(imageData, kernelSize)  {
        const kernel = alg.createMeanKernel(kernelSize)
        return alg.commonFilter(imageData, kernel, kernelSize)
    },
    /**
     * 高斯滤波
     * @param {any} imageData 
     * @param {number} kernelSize 
     * @returns 
     */
    gaussianFilter(imageData, kernelSize) {
        const kernel = alg.createGaussianKernel(kernelSize, 0.5)
        return alg.commonFilter(imageData, kernel, kernelSize)
    },
    /**
     * 获取残差图
     * @param {any} inputData
     * @param {any} outputData
     */
    residualPlot(inputData, outputData, channel = 'r') {
        const { width, height, data } = inputData
        if (width !== outputData.width || height !== outputData.height) {
            throw new RangeError('Residual images must have the same dimensions')
        }
        const offset = channelOffsets[channel]
        if (offset === undefined) throw new RangeError(`Unsupported channel: ${channel}`)
        const length = width * height * 4
        const odata = outputData.data
        const outData = new Uint8ClampedArray(length)
        const residualHistogram = new Uint32Array(256)
        let nonZeroCount = 0
        // 先统计当前通道的非零绝对残差分布。
        for (let i = 0; i < length; i += 4) {
            const residual = Math.abs(data[i + offset] - odata[i + offset])
            residualHistogram[residual]++
            if (residual !== 0) nonZeroCount++
        }
        // 使用非零残差的 P99，避免少量极端值把其余差异压成黑色。
        let percentile99 = 0
        if (nonZeroCount > 0) {
            const targetCount = Math.ceil(nonZeroCount * 0.99)
            let accumulatedCount = 0
            for (let residual = 1; residual < residualHistogram.length; residual++) {
                accumulatedCount += residualHistogram[residual]
                if (accumulatedCount >= targetCount) {
                    percentile99 = residual
                    break
                }
            }
        }
        // 至少以 0~8 作为显示范围，避免只有 1 个灰度级的差异被过度放大。
        const displayMax = Math.max(percentile99, 8)
        for (let i = 0; i < length; i += 4) {
            const residual = Math.abs(data[i + offset] - odata[i + offset])
            const value = Math.min(255, Math.round(residual / displayMax * 255))
            outData[i] = value
            outData[i + 1] = value
            outData[i + 2] = value
            outData[i + 3] = 255
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 反锐化高通滤波 
     * @param {any} imageData 
     * @param {number} kernelSize 
     */
    deSharpFilter(imageData, kernelSize) {
        const kernelData = alg.gaussianFilter(imageData, kernelSize)
        const kdata = kernelData.data
        const { width, height, data } = imageData
        const length = width * height * 4
        const amount = 1.0
        const outData = new Uint8ClampedArray(length)
        for (let i = 0; i < length; i += 4)  {
            outData[i] = data[i] + amount * (data[i] - kdata[i])
            outData[i + 1] = data[i + 1] + amount * (data[i + 1] - kdata[i + 1])
            outData[i + 2] = data[i + 2] + amount * (data[i + 2] - kdata[i + 2])
            outData[i + 3] = data[i + 3]
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 中值滤波
     * @param {any} imageData 
     * @param {*} kernelSize 
     * @returns 
     */
    medianFilter(imageData, kernelSize) {
        const { width, height, data } = imageData
        const outData = new Uint8ClampedArray(width * height * 4)
        const half = Math.floor(kernelSize / 2)
        const total = kernelSize * kernelSize
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const rList = [], gList = [], bList = []
                for (let ky = -half; ky <= half; ky++) {
                    for (let kx = -half; kx <= half; kx++) {
                        const ny = y + ky
                        const nx = x + kx
                        if (ny >= 0 && ny < height && nx >= 0 && nx < width) {
                            const idx = (ny * width + nx) * 4
                            rList.push(data[idx])
                            gList.push(data[idx + 1])
                            bList.push(data[idx + 2])
                        }
                    }
                }
                rList.sort((a, b) => a - b)
                gList.sort((a, b) => a - b)
                bList.sort((a, b) => a - b)
                const index = (y * width + x) * 4
                outData[index]     = rList[Math.floor(rList.length / 2)]
                outData[index + 1] = gList[Math.floor(gList.length / 2)]
                outData[index + 2] = bList[Math.floor(bList.length / 2)]
                outData[index + 3] = data[index + 3]
            }
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 灰度平均
     * @param {any} imageData 
     */
    grayAverage(imageData) {
        const { width, height, data } = imageData
        const length = width * height * 4
        const outData = new Uint8ClampedArray(length) //输出像素
        for (let i = 0; i < length; i += 4) {
            const averageValue = (data[i] + data[i + 1] +
            data[i + 2]) / 3.0
            outData[i] = averageValue
            outData[i + 1] = averageValue
            outData[i + 2] = averageValue
            outData[i + 3] = data[i + 3] 
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 灰度加权平均
     * @param {any} imageData 
     */
    grayWeightedAverage(imageData) {
        const { width, height, data } = imageData
        const length = width * height * 4
        const outData = new Uint8ClampedArray(length) 
        for (let i = 0; i < length; i += 4) {
            const averageValue = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
            outData[i] = averageValue
            outData[i + 1] = averageValue
            outData[i + 2] = averageValue
            outData[i + 3] = data[i + 3] 
        }
        return new ImageData(outData, width, height)
    },
    /**
     * 执行一个可序列化的离散操作，供预览和全尺寸导出共同使用
     */
    applyOperation(imageData, operation) {
        const { type, mode, kernelSize, seed } = operation
        if (type === 'histogram') {
            return mode === 'local' ? alg.limitHistogram(imageData) : alg.histogram(imageData)
        }
        if (type === 'grayscale') {
            return mode === 'weighted' ? alg.grayWeightedAverage(imageData) : alg.grayAverage(imageData)
        }
        if (type === 'noise') {
            if (mode === 'gaussian') return alg.gaussianNoise(imageData, seed)
            if (mode === 'saltPepper') return alg.saltPepperNoise(imageData, seed)
            return alg.speckleNoise(imageData, seed)
        }
        if (type === 'filter') {
            if (mode === 'mean') return alg.meanFilter(imageData, kernelSize)
            if (mode === 'gaussian') return alg.gaussianFilter(imageData, kernelSize)
            if (mode === 'median') return alg.medianFilter(imageData, kernelSize)
            return alg.deSharpFilter(imageData, kernelSize)
        }
        throw new RangeError(`Unsupported operation: ${type}`)
    },
    applyOperations(imageData, operations) {
        return operations.reduce(
            (currentImage, operation) => alg.applyOperation(currentImage, operation),
            imageData
        )
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
