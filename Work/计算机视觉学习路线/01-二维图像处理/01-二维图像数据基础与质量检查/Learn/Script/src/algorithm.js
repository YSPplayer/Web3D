const alg = {
    affineTransform(contrast,brightness,imageData) {
        const { width, height, data } = imageData //data = [r,g,b,a]
        const outData = new Uint8ClampedArray(width * height * 4) //输出像素
        for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = (y * width + x) * 4
            const r = data[index]
            const g = data[index + 1]
            const b = data[index + 2]
            const a = data[index + 3]
            outData[index] = util.clamp(contrast * (r - 128) + 128 + brightness,0,255)
            outData[index + 1] = util.clamp(contrast * (g - 128) + 128 + brightness,0,255)
            outData[index + 2] = util.clamp(contrast * (b - 128) + 128 + brightness,0,255)
            outData[index + 3] = util.clamp(a,0,255)
        }
    }
        return new ImageData(outData, width, height)
    }


}