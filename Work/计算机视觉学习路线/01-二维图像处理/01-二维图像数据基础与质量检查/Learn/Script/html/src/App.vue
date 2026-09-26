<template>
  <div class="learning_page no_select">
    <header class="page_header">
      <div class="header_actions">
        <el-button type="primary" @click="openFileInput">导入图片</el-button>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleFileChange"
        />
      </div>
    </header>

    <main class="workspace">
      <section class="preview_panel panel_surface">

        <div class="preview_grid">
          <article class="media_card">
            <div class="card_header">
              <h3>原图</h3>
              <span class="color_mark original"></span>
            </div>
            <div class="canvas_shell">
              <canvas ref="canvasRoot" class="img_canvas" width="500" height="500"></canvas>
            </div>
          </article>

          <article class="media_card">
            <div class="card_header">
              <h3>结果图</h3>
              <span class="color_mark result"></span>
            </div>
            <div class="canvas_shell">
              <canvas ref="canvasChange" class="img_canvas" width="500" height="500"></canvas>
            </div>
          </article>
        </div>

        <div class="histogram_section">
          <div class="subsection_heading">
            <h2>直方图</h2>
          </div>
          <div class="histogram_grid">
            <article class="histogram_card">
              <div class="histogram_title">
                <div class="histogram_name">
                  <span class="color_mark original"></span>
                  <span>原图</span>
                </div>
                <el-select
                  v-model="rootChannel"
                  :class="['channel_select', `channel_select_${rootChannel}`]"
                  popper-class="channel_select_dropdown"
                  size="small" @change="handleChangeRoot"
                >
                  <el-option class="channel_option channel_option_r" label="R" value="r" />
                  <el-option class="channel_option channel_option_g" label="G" value="g" />
                  <el-option class="channel_option channel_option_b" label="B" value="b" />
                </el-select>
              </div>
              <HistogramChart
                ref="histogramchartRoot"
                :image-datas="imageDatasRoot"
              />
            </article>
            <article class="histogram_card">
              <div class="histogram_title">
                <div class="histogram_name">
                  <span class="color_mark result"></span>
                  <span>结果图</span>
                </div>
                <el-select
                  v-model="changeChannel"
                  :class="['channel_select', `channel_select_${changeChannel}`]"
                  popper-class="channel_select_dropdown"
                  size="small" @change="handleChangeChange"
                >
                  <el-option class="channel_option channel_option_r" label="R" value="r" />
                  <el-option class="channel_option channel_option_g" label="G" value="g" />
                  <el-option class="channel_option channel_option_b" label="B" value="b" />
                </el-select>
              </div>
              <HistogramChart
                ref="histogramchartChange"
                :image-datas="imageDatasChange"
              />
            </article>
          </div>
        </div>
      </section>

      <aside class="control_panel panel_surface">
        <div class="control_heading">
          <h2>参数调整</h2>
        </div>

        <div class="control_list">
          <article class="control_card">
            <div class="control_card_header">
              <h3>对比度</h3>
              <el-button class="reset_button" circle aria-label="复位" @click="resetContrast">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 11a8 8 0 1 0-2.34 5.66M20 5v6h-6" />
                </svg>
              </el-button>
            </div>
            <div class="control_editor">
              <el-slider
                v-model="contrast"
                class="style_slider"
                :min="-5"
                :max="5"
                :step="0.001"
                @input="handleContrastInput"
              />
              <el-input-number
                v-model="contrast"
                :min="-5"
                :max="5"
                :step="0.1"
                :precision="3"
                controls-position="right"
                @change="handleContrastInput"
              />
            </div>
          </article>

          <article class="control_card">
            <div class="control_card_header">
              <h3>亮度</h3>
              <el-button class="reset_button" circle aria-label="复位" @click="resetBrightness">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 11a8 8 0 1 0-2.34 5.66M20 5v6h-6" />
                </svg>
              </el-button>
            </div>
            <div class="control_editor">
              <el-slider
                v-model="brightness"
                class="style_slider"
                :min="-100"
                :max="100"
                :step="0.001"
                @input="handleBrightnessInput"
              />
              <el-input-number
                v-model="brightness"
                :min="-100"
                :max="100"
                :step="1"
                :precision="3"
                controls-position="right"
                @change="handleBrightnessInput"
              />
            </div>
          </article>

          <article class="control_card">
            <div class="control_card_header">
              <h3>伽马亮度</h3>
              <el-button class="reset_button" circle aria-label="复位" @click="resetGamma">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 11a8 8 0 1 0-2.34 5.66M20 5v6h-6" />
                </svg>
              </el-button>
            </div>
            <div class="control_editor">
              <el-slider
                v-model="gamma"
                class="style_slider"
                :min="0.4"
                :max="2.5"
                :step="0.001"
                @input="handleGammaInput"
              />
              <el-input-number
                v-model="gamma"
                :min="0.4"
                :max="2.5"
                :step="0.1"
                :precision="3"
                controls-position="right"
                @change="handleGammaInput"
              />
            </div>
          </article>
        </div>

      </aside>
    </main>
  </div>
</template>
<script setup>
import { computed,onMounted, ref } from 'vue'
import { alg } from './algorithm.js'
import { Type_AffineTransform, Type_Gamma, stateMachine } from './stateMachine.js'
import { store } from './store.js'
import { util } from './util.js'
import HistogramChart from './histogramchart.vue'

const histogramchartRoot = ref(null)
const histogramchartChange = ref(null)
const fileInput = ref(null)
const canvasRoot = ref(null)
const canvasChange = ref(null)
const contrast = ref(1)
const brightness = ref(0)
const gamma = ref(1)
const rootChannel = ref('r')
const changeChannel = ref('r')
const imageDatasRoot = ref(new Array(256).fill(0)) 
const imageDatasChange = ref(new Array(256).fill(0)) 
const updateGetHistogramData =  (target,imageData,type)=> {
    //直方图统计数据更新
    const {r,g,b}  = alg.getHistogramData(imageData)
    if(type === 'r') target.value = r
    else if(type === 'g') target.value = g
    else target.value = b
  
}
const handleChangeRoot = (value)=> {
  updateGetHistogramData(imageDatasRoot,store.imageDataRoot,value)
}
const handleChangeChange = (value) => {
  const ctx = canvasChange.value.getContext('2d')
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  updateGetHistogramData(imageDatasChange,imageData,value)
}
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
  updateGetHistogramData(imageDatasChange,imageData,changeChannel.value)

}

const resetData = () => {
  store.imageDataRoot = util.getCanvasImageData(canvasRoot.value)
  stateMachine.resetState()
  updateGetHistogramData(imageDatasRoot,store.imageDataRoot,rootChannel.value)
  updateGetHistogramData(imageDatasChange,store.imageDataRoot,changeChannel.value)
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

const resetContrast = () => {
  contrast.value = 1
  handleContrastInput()
}

const resetBrightness = () => {
  brightness.value = 0
  handleBrightnessInput()
}

const resetGamma = () => {
  gamma.value = 1
  handleGammaInput()
}

onMounted(() => {
  stateMachine.resetState()
})
</script>
<style>
:root {
  color: #172033;
  background: #f3f6fb;
  font-family:
    Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  font-synthesis: none;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  min-width: 320px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 0%, rgba(64, 158, 255, 0.1), transparent 30%),
    #f3f6fb;
}

button,
input {
  font: inherit;
}

.learning_page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page_header,
.workspace {
  width: 100%;
}

.page_header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid #dfe6ef;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 8px rgba(28, 47, 78, 0.04);
}

.page_header h1 {
  color: #162033;
  font-size: 19px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.header_actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.workspace {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  align-items: stretch;
  gap: 0;
  overflow: hidden;
}

.panel_surface {
  background: #fff;
}

.preview_panel {
  min-width: 0;
  min-height: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) minmax(190px, 0.58fr);
  gap: 16px;
  padding: 18px 20px;
  overflow: hidden;
  background: #f3f6fb;
}

.section_heading,
.control_heading,
.subsection_heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.section_heading h2,
.control_heading h2,
.subsection_heading h2 {
  color: #1d2939;
  font-size: 16px;
  line-height: 1.3;
}

.preview_grid,
.histogram_grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  min-height: 0;
}

.preview_grid {
  margin-top: 0;
}

.media_card,
.histogram_card {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid #e7ecf3;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(28, 47, 78, 0.05);
}

.media_card,
.histogram_card {
  display: flex;
  flex-direction: column;
}

.card_header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e7ecf3;
  background: #fff;
}

.card_header h3 {
  color: #253149;
  font-size: 14px;
}

.color_mark {
  display: inline-block;
  width: 9px;
  height: 9px;
  flex: 0 0 9px;
  border-radius: 50%;
}

.color_mark.original {
  background: #8795a9;
  box-shadow: 0 0 0 4px rgba(135, 149, 169, 0.13);
}

.color_mark.result {
  background: #409eff;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.13);
}

.canvas_shell {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    linear-gradient(45deg, #1c2430 25%, transparent 25%),
    linear-gradient(-45deg, #1c2430 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1c2430 75%),
    linear-gradient(-45deg, transparent 75%, #1c2430 75%),
    #151b24;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
}

.img_canvas {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  aspect-ratio: 1;
  background: transparent;
}

.histogram_section {
  min-height: 0;
  display: flex;
  margin-top: 0;
  padding-top: 14px;
  flex-direction: column;
  border-top: 1px solid #e9eef5;
}

.histogram_grid {
  flex: 1;
  margin-top: 10px;
}

.histogram_title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 40px;
  gap: 12px;
  padding: 8px 12px 0;
  color: #46536a;
  font-size: 13px;
  font-weight: 650;
}

.histogram_name {
  display: flex;
  align-items: center;
  gap: 9px;
}

.channel_select {
  width: 72px;
}

.channel_select .el-select__wrapper {
  min-height: 28px;
  border-radius: 8px;
  background: #f7f9fc;
  box-shadow: 0 0 0 1px #e0e6ef inset;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}

.channel_select .el-select__wrapper:hover,
.channel_select .el-select__wrapper.is-focused {
  background: #fff;
  box-shadow: 0 0 0 1px #409eff inset;
}

.channel_select .el-select__selected-item {
  font-weight: 700;
  text-align: center;
}

.channel_select_r .el-select__selected-item {
  color: #e5484d;
}

.channel_select_g .el-select__selected-item {
  color: #2f9e62;
}

.channel_select_b .el-select__selected-item {
  color: #3578e5;
}

.channel_select_dropdown .el-select-dropdown__item {
  height: 30px;
  padding: 0 12px;
  line-height: 30px;
  font-weight: 700;
  text-align: center;
}

.channel_select_dropdown .channel_option_r {
  color: #e5484d;
}

.channel_select_dropdown .channel_option_g {
  color: #2f9e62;
}

.channel_select_dropdown .channel_option_b {
  color: #3578e5;
}

.channel_select_dropdown .el-select-dropdown__item.is-selected {
  background: #edf5ff;
}

.control_panel {
  position: sticky;
  top: 0;
  align-self: start;
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: 22px 20px;
  overflow-y: auto;
  border-left: 1px solid #dfe6ef;
}

.control_heading {
  padding-bottom: 18px;
  border-bottom: 1px solid #e9eef5;
}

.control_list {
  display: flex;
  margin-top: 18px;
  flex-direction: column;
  gap: 14px;
}

.control_card {
  padding: 15px;
  border: 1px solid #e7ecf3;
  border-radius: 13px;
  background: #fafcff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.control_card:focus-within,
.control_card:hover {
  border-color: #cfe3fb;
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.08);
}

.control_card_header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.control_card_header h3 {
  color: #27344b;
  font-size: 14px;
}

.reset_button.el-button {
  width: 28px;
  height: 28px;
  padding: 0;
  border-color: transparent;
  color: #7e8ba0;
  background: transparent;
}

.reset_button.el-button:hover,
.reset_button.el-button:focus-visible {
  border-color: #cfe3fb;
  color: #409eff;
  background: #edf6ff;
}

.reset_button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.control_editor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  align-items: center;
  gap: 15px;
  margin-top: 13px;
}

.style_slider {
  width: 100%;
}

.style_slider:hover {
  cursor: pointer;
}

.control_editor .el-input-number {
  width: 112px;
}

.no_select {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.control_editor input {
  user-select: text;
  -webkit-user-select: text;
}

@media (max-width: 1260px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .control_panel {
    position: static;
    min-height: auto;
    border-top: 1px solid #dfe6ef;
    border-left: 0;
  }

  .control_list {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .page_header {
    min-height: 58px;
    padding: 0 14px;
  }

  .header_actions {
    width: 100%;
    justify-content: space-between;
  }

  .preview_grid,
  .histogram_grid,
  .control_list {
    grid-template-columns: 1fr;
  }

  .preview_panel,
  .control_panel {
    padding: 16px;
  }
}

@media (max-width: 460px) {
  .header_actions {
    justify-content: flex-end;
  }

  .control_editor {
    grid-template-columns: 1fr;
  }

  .control_editor .el-input-number {
    width: 100%;
  }
}
</style>
