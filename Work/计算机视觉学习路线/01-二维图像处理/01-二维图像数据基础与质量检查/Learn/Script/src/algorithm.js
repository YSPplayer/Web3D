const alg = {
   processAny(imageData,func,...args) {
        const { width, height, data } = imageData //data = [r,g,b,a]
        const outData = new Uint8ClampedArray(width * height * 4) //输出像素
        for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = (y * width + x) * 4
            const r = data[index]
            const g = data[index + 1]
            const b = data[index + 2]
            const a = data[index + 3]
            outData[index] = func(r,...args)
            outData[index + 1] = func(g,...args)
            outData[index + 2] = func(b,...args)
            outData[index + 3] = util.clamp(a,0,255)
        }
        }
        return new ImageData(outData, width, height)
    },
    affineTransformProcess(value,contrast,brightness) {
        return util.clamp(contrast * (value - 128) + 128 + brightness,0,255)
    },
    gammaProcess(value,gamma) {
        value = value / 255.0
        value = Math.pow(value,gamma)
        return util.clamp(value,0,255)
    },
    /**
     * 修改图像的亮度/对比度
     * @param {any} imageData 
     * @param {number} contrast 
     * @param {number} brightness 
     * @returns 
     */
    affineTransform(imageData,contrast,brightness) {
       return alg.processAny(imageData,alg.affineTransformProcess,contrast,brightness)
    },
    /**
     * 修改图像的伽马亮度
     * @param {any} imageData 
     * @param {number} gamma 
     * @returns 
     */
    gamma(imageData,gamma) {
        return alg.processAny(imageData,alg.gammaProcess,gamma)
    }

 
}