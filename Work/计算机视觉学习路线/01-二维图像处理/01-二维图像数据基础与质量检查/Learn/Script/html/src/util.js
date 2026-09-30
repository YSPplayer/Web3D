const util = {
    drawImageToCanvas(canvas,img) {
    const ctx = canvas.getContext('2d')
    // 清空 canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    // 计算缩放比例（保持宽高比，铺满 canvas）
    const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
    )
     // 计算绘制尺寸
    const drawWidth = img.width * scale
    const drawHeight = img.height * scale
    // 计算居中位置
    const offsetX = (canvas.width - drawWidth) / 26
    const offsetY = (canvas.height - drawHeight) / 2
    // 绘制
    ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

    },
    getCanvasImageData(canvas) {
    const ctx = canvas.getContext('2d')
    //获取到当前视口的canvas像素
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    return imageData
    },
    clamp(value, min, max)  {
        return Math.min(max, Math.max(min, value))
    },
    //创建一个空的二维数组
    createArray2(y,x) {
        const tiles = []
        for (let i = 0; i < y; i++) {
            arr[i] = [];
            for (let j = 0; j < x; j++) {
                arr[i][j] = {};
            }
        }
        return tiles
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
    }
    
}

export { util }
