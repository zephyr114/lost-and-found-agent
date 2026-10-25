import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/items',
      name: 'items',
      component: () => import('@/views/ItemsView.vue'),
    },
    {
      path: '/items/:id(\\d+)',
      name: 'itemDetail',
      component: () => import('@/views/ItemDetailView.vue'),
    },
    {
      path: '/publish/lost',
      name: 'publishLost',
      component: () => import('@/views/ItemFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/publish/found',
      name: 'publishFound',
      component: () => import('@/views/ItemFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/items/:id(\\d+)/edit',
      name: 'itemEdit',
      component: () => import('@/views/ItemFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my/items',
      name: 'myItems',
      component: () => import('@/views/MyItemsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/items/:id(\\d+)/claim',
      name: 'claimForm',
      component: () => import('@/views/ClaimFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my/claims',
      name: 'myClaims',
      component: () => import('@/views/MyClaimsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my/claims/received',
      name: 'receivedClaims',
      component: () => import('@/views/ReceivedClaimsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('@/views/MessagesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/matches',
      name: 'matches',
      component: () => import('@/views/MatchResultsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/items/:id(\\d+)/matches',
      name: 'itemMatches',
      component: () => import('@/views/MatchResultsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: '', name: 'adminDashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
        { path: 'items', name: 'adminItems', component: () => import('@/views/admin/AdminItems.vue') },
        { path: 'users', name: 'adminUsers', component: () => import('@/views/admin/AdminUsers.vue') },
        { path: 'claims', name: 'adminClaims', component: () => import('@/views/admin/AdminClaims.vue') },
        { path: 'reports', name: 'adminReports', component: () => import('@/views/admin/AdminReports.vue') },
        { path: 'announcements', name: 'adminAnnouncements', component: () => import('@/views/admin/AdminAnnouncements.vue') },
        { path: 'agent-logs', name: 'adminAgentLogs', component: () => import('@/views/admin/AdminAgentLogs.vue') },
        { path: 'logs', name: 'adminLogs', component: () => import('@/views/admin/AdminOperationLogs.vue') },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// 全局路由守卫：登录态与角色权限
router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    return { name: 'home' }
  }
  if (to.meta.guestOnly && userStore.isLoggedIn) {
    return { name: 'home' }
  }
})

export default router
