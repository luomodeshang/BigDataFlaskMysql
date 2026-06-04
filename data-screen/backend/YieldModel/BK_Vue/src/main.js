import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@fortawesome/fontawesome-free/css/all.css'
import * as echarts from 'echarts';
axios.defaults.baseURL = 'http://localhost:5000' // 全局生效

const app = createApp(App)
app.config.globalProperties.$axios = axios


app.use(router)
app.use(ElementPlus)
app.mount('#app')
