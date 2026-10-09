<template>
  <div class="residual_canvas_shell">
    <canvas
      ref="canvas"
      class="residual_canvas"
      width="500"
      height="500"
    ></canvas>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  imageData: {
    type: Object,
    default: null
  },
  staticBlack: {
    type: Boolean,
    default: false
  }
})

const canvas = ref(null)

const drawImageData = (imageData = props.imageData) => {
  const targetCanvas = canvas.value
  if (!targetCanvas) return

  const targetContext = targetCanvas.getContext('2d')
  targetContext.clearRect(0, 0, targetCanvas.width, targetCanvas.height)
  if (props.staticBlack) {
    targetContext.fillStyle = '#000'
    targetContext.fillRect(0, 0, targetCanvas.width, targetCanvas.height)
    return
  }
  if (!imageData) return

  const sourceCanvas = document.createElement('canvas')
  sourceCanvas.width = imageData.width
  sourceCanvas.height = imageData.height
  sourceCanvas.getContext('2d').putImageData(imageData, 0, 0)

  const scale = Math.min(
    targetCanvas.width / sourceCanvas.width,
    targetCanvas.height / sourceCanvas.height
  )
  const drawWidth = sourceCanvas.width * scale
  const drawHeight = sourceCanvas.height * scale
  const offsetX = (targetCanvas.width - drawWidth) / 2
  const offsetY = (targetCanvas.height - drawHeight) / 2

  targetContext.drawImage(sourceCanvas, offsetX, offsetY, drawWidth, drawHeight)
}

watch(
  [() => props.imageData, () => props.staticBlack],
  () => drawImageData()
)

onMounted(() => drawImageData())

defineExpose({
  canvas,
  drawImageData
})
</script>

<style scoped>
.residual_canvas_shell {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* background:
    linear-gradient(45deg, #1c2430 25%, transparent 25%),
    linear-gradient(-45deg, #1c2430 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1c2430 75%),
    linear-gradient(-45deg, transparent 75%, #1c2430 75%),
    #151b24; */
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
}

.residual_canvas {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
}
</style>
