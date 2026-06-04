import { createRouter, createWebHistory } from 'vue-router'
import PredictionPage from '../views/PredictionPage.vue'
import YieldPage from '../views/YieldPage.vue'
import DiagnosisPage from '../views/DiagnosisPage.vue'
import RealtimePage from '../views/RealtimePage.vue'
const routes = [

  {
    path: '/prediction',
    name: 'Prediction',
    component: PredictionPage
  },
  {
    path: '/yield',
    name: 'Yield',
    component: YieldPage
  },
  {
    path: '/',
    redirect: '/prediction'
  },
  {
    path: '/diagnosis',
    name: 'Diagnosis',
    component: DiagnosisPage,
    meta: {
      title: '故障诊断'
       },
  },

  {
    path: '/realtime',
    name: 'Realtime',
    component: RealtimePage,
    meta: {
      title: '实时监测'
       },
  }

]

const router = createRouter({
  history: createWebHistory(),  // 移除了 process.env.BASE_URL
  routes
})

export default router
