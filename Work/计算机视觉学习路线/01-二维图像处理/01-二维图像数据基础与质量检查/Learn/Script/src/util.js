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
    }
}