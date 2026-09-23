
const render = () => {
    const algargs = {
       contrast: Number(labelContrast.textContent),
       brightness:Number(labelBrightness.textContent),
       gamma:Number(labelGamma.textContent)
    }
    alg.updateArgs(algargs)
    if(store.imageData === null) return 
    const ctx = canvasChange.getContext('2d')
    const imageData = alg.render(store.imageDataRoot)
    ctx.putImageData(imageData, 0, 0)
}
const resetData = ()=> {
    //更新数据图像
    store.imageDataRoot = util.getCanvasImageData(canvasRoot)
    //重置状态机状态
    stateMachine.resetState()
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
                resetData()
            }
            img.src = event.target.result
        }
        reader.readAsDataURL(file)
    });
    sliderContrast.addEventListener('input',(e) => { //对比度调整
        labelContrast.textContent = sliderContrast.value
        stateMachine.pushState(Type_AffineTransform)
        render()
    });
    sliderBrightness.addEventListener('input',(e) => { //对比度调整
        labelBrightness.textContent = sliderBrightness.value
        stateMachine.pushState(Type_AffineTransform)
        render()
    });
    sliderGamma.addEventListener('input',(e) => { //伽马亮度调整
        labelGamma.textContent = sliderGamma.value
        stateMachine.pushState(Type_Gamma)
        render()
    })
}



window.onload = ()=> {
    init()
}
