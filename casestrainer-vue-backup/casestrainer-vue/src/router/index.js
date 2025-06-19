import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

import ApiTest from '../views/ApiTest.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/enhanced-validator'
  },
  {
    path: '/api-test',
    name: 'ApiTest',
    component: ApiTest
  },
  {
    path: '/enhanced-validator',
    name: 'EnhancedValidator',
    component: () => import('../views/EnhancedValidator.vue')
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
    path: '/about',
    name: 'About',
    component: () => import('../views/About.vue')
  },
  {
    path: '/backend-test',
    name: 'BackendTest',
    component: () => import('../views/BackendTest.vue')
  }
]

const router = createRouter({
  history: createWebHistory('/casestrainer/'),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top when navigating
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  }
});

export default router;
