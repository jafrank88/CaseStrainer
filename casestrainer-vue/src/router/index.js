import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/unconfirmed-citations',
    name: 'UnconfirmedCitations',
    component: () => import('../views/UnconfirmedCitations.vue')
  },
  {
    path: '/multitool-confirmed',
    name: 'MultitoolConfirmed',
    component: () => import('../views/MultitoolConfirmed.vue')
  },
  {
    path: '/citation-network',
    name: 'CitationNetwork',
    component: () => import('../views/CitationNetwork.vue')
  },
  {
    path: '/ml-classifier',
    name: 'MLClassifier',
    component: () => import('../views/MLClassifier.vue')
  },
  {
    path: '/citation-tester',
    name: 'CitationTester',
    component: () => import('../views/CitationTester.vue')
  },
  {
    path: '/enhanced-validator',
    name: 'EnhancedValidator',
    component: () => import('../views/EnhancedValidator.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/About.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
