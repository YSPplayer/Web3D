<template>
  <div class="main_div flex_column_center no_select" style="gap: 1rem">
    <div>
      <el-button type="primary" @click="openFileInput">导入图片</el-button>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        style="display: none"
        @change="handleFileChange"
      />
    </div>
    <div class="flex_row" style="gap: 1rem">
      <div class="flex_column">
          <div class="flex_row" style="gap: 1rem">
             <canvas ref="canvasRoot" class="img_canvas" width="500" height="500"></canvas>
            <canvas ref="canvasChange" class="img_canvas" width="500" height="500"></canvas>
          </div>
           <div class="flex_row" style="gap: 1rem">
              <histogramchart :imageDatas="imageDatasRoot" ref="histogramchartRoot" > 
              </histogramchart>
                <!-- <histogramchart/>
                <histogramchart/> -->
           </div>
      </div>
     
      <div class="flex_column_center">
        <div class="flex_row" style="gap: 0.5rem">
          <label class="label_fixed">对比度</label>
          <el-slider
            v-model="contrast"
            class="style_slider"
            :min="-5"
            :max="5"
            :step="0.001"
            @input="handleContrastInput"
          />
          <label class="label_fixed_left">{{ contrast }}</label>
        </div>
        <div class="flex_row" style="gap: 0.5rem">
          <label class="label_fixed">亮度</label>
          <el-slider
            v-model="brightness"
            class="style_slider"
            :min="-100"
            :max="100"
            :step="0.001"
            @input="handleBrightnessInput"
          />
          <label class="label_fixed_left">{{ brightness }}</label>
        </div>
        <div class="flex_row" style="gap: 0.5rem">
          <label class="label_fixed">伽马亮度</label>
          <el-slider
            v-model="gamma"
            class="style_slider"
            :min="0.4"
            :max="2.5"
            :step="0.001"
            @input="handleGammaInput"
          />
          <label class="label_fixed_left">{{ gamma }}</label>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { alg } from './algorithm.js'
import { Type_AffineTransform, Type_Gamma, stateMachine } from './stateMachine.js'
import { store } from './store.js'
import { util } from './util.js'
import histogramchart  from './histogramchart.vue'

const histogramchartRoot = ref(null)
const fileInput = ref(null)
const canvasRoot = ref(null)
const canvasChange = ref(null)
const contrast = ref(1)
const brightness = ref(0)
const gamma = ref(1)
const imageDatasRoot = ref([]) 

const render = () => {
  alg.updateArgs({
    contrast: Number(contrast.value),
    brightness: Number(brightness.value),
    gamma: Number(gamma.value),
  })
  if (store.imageDataRoot === null) return

  const ctx = canvasChange.value.getContext('2d')
  const imageData = alg.render(store.imageDataRoot)
  ctx.putImageData(imageData, 0, 0)
  //直方图统计数据更新
    const {r,g,b}  = alg.getHistogramData(imageData)
    imageDatasRoot.value = r
}

const resetData = () => {
  store.imageDataRoot = util.getCanvasImageData(canvasRoot.value)
  stateMachine.resetState()
}

const openFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (readerEvent) => {
    const img = new Image()
    img.onload = () => {
      util.drawImageToCanvas(canvasRoot.value, img)
      util.drawImageToCanvas(canvasChange.value, img)
      resetData()
    }
    img.src = readerEvent.target.result
  }
  reader.readAsDataURL(file)
}

const handleContrastInput = () => {
  stateMachine.pushState(Type_AffineTransform)
  render()
}

const handleBrightnessInput = () => {
  stateMachine.pushState(Type_AffineTransform)
  render()
}

const handleGammaInput = () => {
  stateMachine.pushState(Type_Gamma)
  render()
}

onMounted(() => {
  stateMachine.resetState()
})
</script>
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.main_div {
  width: 100vw;
  height: 100vh;
}

.flex_column_center {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.flex_row_center {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: row;
}

.flex_column {
  display: flex;
  flex-direction: column;
}

.flex_row {
  display: flex;
  flex-direction: row;
}

.img_canvas {
  width: 500px;
  height: 500px;
  background-color: black;
}

.style_slider {
  width: 180px;
}

.style_slider:hover {
  cursor: pointer;
}

.label_fixed {
  width: 4rem;
  text-align: right;
  flex-shrink: 0;
}

.label_fixed_left {
  width: 3em;
  text-align: left;
  flex-shrink: 0;
}

.no_select {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
</style>
