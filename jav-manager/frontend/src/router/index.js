import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '首页', icon: 'Home' }
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/Library.vue'),
    meta: { title: '影片库', icon: 'Film' }
  },
  {
    path: '/charts',
    name: 'Charts',
    component: () => import('../views/ChartList.vue'),
    meta: { title: '榜单中心', icon: 'Trophy' }
  },
  {
    path: '/charts/:name',
    name: 'ChartDetail',
    component: () => import('../views/ChartDetail.vue'),
    meta: { title: '榜单详情' }
  },
  {
    path: '/charts/:name/gaps',
    name: 'GapAnalysis',
    component: () => import('../views/GapAnalysis.vue'),
    meta: { title: '缺口分析' }
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('../views/Discover.vue'),
    meta: { title: '发现', icon: 'Compass' }
  },
  {
    path: '/todo',
    name: 'Todo',
    component: () => import('../views/TodoList.vue'),
    meta: { title: '待看清单', icon: 'List' }
  },
  {
    path: '/actors',
    name: 'Actors',
    component: () => import('../views/ActorList.vue'),
    meta: { title: '演员', icon: 'User' }
  },
  {
    path: '/actors/:name',
    name: 'ActorDetail',
    component: () => import('../views/ActorDetail.vue'),
    meta: { title: '演员详情' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { title: '设置', icon: 'Setting' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - JAV Manager` : 'JAV Manager'
  next()
})

export default router
