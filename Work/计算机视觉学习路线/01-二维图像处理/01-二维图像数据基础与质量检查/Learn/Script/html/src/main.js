import { createApp } from 'vue'
import { ElButton, ElSlider } from 'element-plus'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/slider/style/css'
import App from './App.vue'

createApp(App)
  .component('ElButton', ElButton)
  .component('ElSlider', ElSlider)
  .mount('#app')
