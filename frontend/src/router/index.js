import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页概览' }
  },
  {
    path: '/lens',
    name: 'LensLibrary',
    component: () => import('@/views/LensLibrary.vue'),
    meta: { title: '镜片库' }
  },
  {
    path: '/records',
    name: 'WearRecords',
    component: () => import('@/views/WearRecords.vue'),
    meta: { title: '佩戴记录' }
  },
  {
    path: '/comfort',
    name: 'ComfortTracking',
    component: () => import('@/views/ComfortTracking.vue'),
    meta: { title: '舒适度追踪' }
  },
  {
    path: '/expiry',
    name: 'ExpiryWarning',
    component: () => import('@/views/ExpiryWarning.vue'),
    meta: { title: '过期预警' }
  },
  {
    path: '/stats',
    name: 'Statistics',
    component: () => import('@/views/Statistics.vue'),
    meta: { title: '统计分析' }
  },
  {
    path: '/outfit-plans',
    name: 'OutfitPlans',
    component: () => import('@/views/OutfitPlans.vue'),
    meta: { title: '妆容搭配计划' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '彩瞳追踪'} - 个人彩瞳管理平台`
  next()
})

export default router
