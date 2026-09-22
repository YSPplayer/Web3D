const affineTransform = ()=> {
    if(store.imageData === null) return 
    const contrast = Number(labelContrast.textContent)
    const brightness = Number(labelBrightness.textContent)
    const ctx = canvasChange.getContext('2d')
    const imageData = alg.affineTransform(contrast,brightness,store.imageData)
    ctx.putImageData(imageData, 0, 0)
}
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
                util.drawImageToCanvas(canvasRoot,img)
                util.drawImageToCanvas(canvasChange,img)
                store.imageData = util.getCanvasImageData(canvasRoot)
            }
            img.src = event.target.result
        }
        reader.readAsDataURL(file)
    });
    sliderContrast.addEventListener('input',(e) => { //对比度调整
        labelContrast.textContent = sliderContrast.value
        affineTransform()
    });
    sliderBrightness.addEventListener('input',(e) => { //对比度调整
        labelBrightness.textContent = sliderBrightness.value
        affineTransform()
    })
}



window.onload = ()=> {
    init()
}
