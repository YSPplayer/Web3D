
const init = ()=> {
     uiInit()
     uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
         // 1. 用 FileReader 读取文件
        const reader = new FileReader()
        reader.onload = (event) => {
            // 2. 创建 Image 对象
            const img = new Image()
            img.onload = () => {
                // 3. 图片加载完，绘制到 canvas
                drawImageToCanvas(canvasRoot,img)
            }
            img.src = event.target.result
        }
        reader.readAsDataURL(file)
    });
}

const drawImageToCanvas = (canvas,img) => {
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
    const offsetX = (canvas.width - drawWidth) / 2
    const offsetY = (canvas.height - drawHeight) / 2
    // 绘制
    ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

}

window.onload = ()=> {
    init()
}
