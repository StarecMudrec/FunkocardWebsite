import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Login from '@/components/Login.vue'
import CardDetail from '@/views/CardDetail.vue'
import AddCard from '@/views/AddCard.vue'
import CategoryCards from '@/views/CategoryCards.vue'
import useStore from 'vuex'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/home',
    redirect: '/'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/card/:id',
    name: 'CardDetail',
    component: CardDetail,
    props: true
  },
  {
    path: '/add-card',
    name: 'AddCard',
    component: AddCard
  },
  {
    path: '/category/:categoryId',
    name: 'Category',
    component: CategoryCards,
    props: true
  },
  {
    path: '/logout',
    beforeEnter: (to, from, next) => {
      next('/')
    }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/About.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior (to, from, savedPosition) {
    // Don't scroll to top when navigating between card detail and category
    if ((from.name === 'Category' && to.name === 'CardDetail') || 
        (from.name === 'CardDetail' && to.name === 'Category')) {
      return false
    }
    return { top: 0 }
  }
})

// Add navigation guards to track navigation type
router.beforeEach((to, from, next) => {
  // Set navigation type based on route changes
  if (from.name === 'Category' && to.name === 'CardDetail') {
    to.meta.navigationType = 'to-card-detail'
  } else if (from.name === 'CardDetail' && to.name === 'Category') {
    to.meta.navigationType = 'to-category'
  } else if (to.name === 'CardDetail' && from.name === 'Category') {
    sessionStorage.setItem('previousCategory', from.params.categoryId);
  } else {
    to.meta.navigationType = 'other'
  }

  
  const store = useStore()
  
  if (to.meta.requiresAuth && !store.state.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
  
  next()
})

export default router
