import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/home/HomePage.vue')
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('@/views/admin/LoginPage.vue')
    },
    {
      path: '/admin',
      redirect: '/admin/dashboard',
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: () => import('@/views/admin/DashboardPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/keywords',
      name: 'admin-keywords',
      component: () => import('@/views/admin/KeywordsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/videos',
      name: 'admin-videos',
      component: () => import('@/views/admin/VideosPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/tasks',
      name: 'admin-tasks',
      component: () => import('@/views/admin/TasksPage.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'admin-login' })
  } else {
    next()
  }
})

export default router
