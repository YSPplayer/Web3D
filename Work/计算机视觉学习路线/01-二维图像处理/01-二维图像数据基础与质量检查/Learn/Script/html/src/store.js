const store = {
    sourceImageDataFull: null, // 仅用于导出时重放处理链的全尺寸原图
    imageDataRoot: null, // 缩放后的预览原图
    imageDataShot: null, // 已提交离散操作后的预览快照
    imageDataResult: null, // 当前用户看到的预览结果
    operations: [] // 可在全尺寸原图上重放的离散操作
}

export { store }
