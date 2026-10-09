const util = {
    clamp(value, min, max)  {
        return Math.min(max, Math.max(min, value))
    },
    /**
     * 生成恒等 LUT
     * 输入是多少，输出还是多少
     */
    createIdentityLut() {
        const lut = new Uint8Array(256)
        for (let i = 0; i < 256; i++) {
            lut[i] = i
        }
        return lut
    },
    /*
        根据一个通道的直方图生成均衡化LUT
    */
    createEqualizeLut(histogram, pixelCount) {
        if (pixelCount === 0) {
            return util.createIdentityLut()
        }
        const lut = new Uint8Array(256)
        let cdf = 0
        let cdfMin = 0
        for (let i = 0; i < 256; i++) {
            cdf += histogram[i]

            if (cdfMin === 0 && cdf > 0) {
                cdfMin = cdf
            }
        }
        const denominator = pixelCount - cdfMin
        // 整个区域只有一种像素值时，保持原值
        if (denominator <= 0) {
            return util.createIdentityLut()
        }
        cdf = 0
        for (let i = 0; i < 256; i++) {
            cdf += histogram[i]
            const mappedValue = Math.round(
                ((cdf - cdfMin) / denominator) * 255
            )
            lut[i] = Math.max(
                0,
                Math.min(255, mappedValue)
            )
        }
        return lut
    },
    /*
    双线性插值
    */
    bilinear(value00,value10,value01,value11,fx,fy) {
        const top = value00 + (value10 - value00) * fx
        const bottom = value01 + (value11 - value01) * fx
        return Math.round(top + (bottom - top) * fy)
    },
    /*
      RGB转HSV  
    */
   rgbToHsv(r, g, b) {
        r /= 255
        g /= 255
        b /= 255
        const max = Math.max(r, g, b)
        const min = Math.min(r, g, b)
        const delta = max - min
        let h = 0
        const v = max
        const s = max === 0 ? 0 : delta / max
        if (delta !== 0) {
            if (max === r) {
            h = 60 * (((g - b) / delta) % 6)
            } else if (max === g) {
            h = 60 * ((b - r) / delta + 2)
            } else {
            h = 60 * ((r - g) / delta + 4)
            }
            if (h < 0) h += 360
        }
        return { h, s, v }
    },
    /*
    HSV转RGB
    */
   hsvToRgb(h, s, v) {
        h = ((h % 360) + 360) % 360   // 保证 0-360
        const c = v * s
        const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
        const m = v - c
        let r = 0, g = 0, b = 0
        if (h < 60)       { r = c; g = x; b = 0 }
        else if (h < 120) { r = x; g = c; b = 0 }
        else if (h < 180) { r = 0; g = c; b = x }
        else if (h < 240) { r = 0; g = x; b = c }
        else if (h < 300) { r = x; g = 0; b = c }
        else              { r = c; g = 0; b = x }
        return {
            r: Math.round((r + m) * 255),
            g: Math.round((g + m) * 255),
            b: Math.round((b + m) * 255)
        }
   },
   /*
   gaussian正态分布噪音
   */
   createSeededRandom(seed) {
        let state = seed >>> 0
        return () => {
            state += 0x6D2B79F5
            let value = state
            value = Math.imul(value ^ value >>> 15, value | 1)
            value ^= value + Math.imul(value ^ value >>> 7, value | 61)
            return ((value ^ value >>> 14) >>> 0) / 4294967296
        }
   },
   gaussianRandom(mean = 0, sigma = 1, random = Math.random) {
        let u1 = random()
        let u2 = random()
        // 避免 log(0)
        if (u1 === 0) u1 = 1e-10
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
        return mean + z * sigma
   },
    sumArray(arr) {
        let sum = 0
        for (let i = 0; i < arr.length; i++) {
            sum += arr[i]
        }
        return sum
    }
}

export { util }
