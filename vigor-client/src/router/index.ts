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
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/admin/dashboard'
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/DashboardPage.vue')
        },
        {
          path: 'categories',
          name: 'admin-categories',
          component: () => import('@/views/admin/CategoriesPage.vue')
        },
        {
          path: 'keywords',
          name: 'admin-keywords',
          component: () => import('@/views/admin/KeywordsPage.vue')
        },
        {
          path: 'videos',
          name: 'admin-videos',
          component: () => import('@/views/admin/VideosPage.vue')
        },
        {
          path: 'tasks',
          name: 'admin-tasks',
          component: () => import('@/views/admin/TasksPage.vue')
        },
        {
          path: 'scheduled-tasks',
          name: 'admin-scheduled-tasks',
          component: () => import('@/views/admin/ScheduledTasksPage.vue')
        }
      ]
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
