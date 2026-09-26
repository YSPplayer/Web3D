import { createApp } from 'vue'
import { ElButton, ElInputNumber, ElOption, ElSelect, ElSlider } from 'element-plus'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/input-number/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/slider/style/css'
import App from './App.vue'

createApp(App)
  .component('ElButton', ElButton)
  .component('ElInputNumber', ElInputNumber)
  .component('ElOption', ElOption)
  .component('ElSelect', ElSelect)
  .component('ElSlider', ElSlider)
  .mount('#app')
