import { createRouter, createWebHistory } from 'vue-router';

// Base path for the application
const BASE_PATH = import.meta.env.BASE_URL || '/casestrainer/';

// Import views with lazy loading for better performance
const HomeView = () => import('@/views/HomeView.vue');
const EnhancedValidator = () => import('@/views/EnhancedValidator.vue');
const MinimalTest = () => import('@/views/MinimalTest.vue');
const NotFound = () => import('@/views/NotFound.vue');
const BrowserExtension = () => import('@/views/BrowserExtension.vue');
const WordPlugin = () => import('@/views/WordPlugin.vue');
const ApiDocs = () => import('@/views/ApiDocs.vue');
const Docs = () => import('@/views/Docs.vue');

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: {
      title: 'CaseStrainer - Legal Citation Validator',
      metaTags: [
        {
          name: 'description',
          content: 'Validate, analyze, and manage legal citations with CaseStrainer. The powerful tool for legal professionals.'
        },
        {
          property: 'og:title',
          content: 'CaseStrainer - Legal Citation Validator'
        },
        {
          property: 'og:description',
          content: 'Validate, analyze, and manage legal citations with CaseStrainer. The powerful tool for legal professionals.'
        },
        {
          property: 'og:type',
          content: 'website'
        }
      ]
    }
  },
  {
    path: '/docs',
    name: 'Docs',
    component: Docs,
    meta: {
      title: 'Documentation | CaseStrainer',
      metaTags: [
        { name: 'description', content: 'Documentation hub for CaseStrainer, including user guides, API docs, and more.' }
      ]
    }
  },
  {
    path: '/docs/api',
    name: 'ApiDocs',
    component: ApiDocs,
    meta: {
      title: 'API Documentation | CaseStrainer',
      metaTags: [
        { name: 'description', content: 'API documentation for CaseStrainer.' }
      ]
    }
  },
  {
    path: '/browser-extension',
    name: 'BrowserExtension',
    component: BrowserExtension,
    meta: {
      title: 'Browser Extension | CaseStrainer',
      metaTags: [
        { name: 'description', content: 'Install the CaseStrainer browser extension to validate citations directly on the web.' }
      ]
    }
  },
  {
    path: '/word-plugin',
    name: 'WordPlugin',
    component: WordPlugin,
    meta: {
      title: 'Word Plug-in | CaseStrainer',
      metaTags: [
        { name: 'description', content: 'Use the CaseStrainer Word plug-in to validate citations directly in your documents.' }
      ]
    }
  },

  // Catch-all route for 404s
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '404 - Page Not Found | CaseStrainer'
    }
  }
];

const router = createRouter({
  history: createWebHistory(BASE_PATH),
  base: BASE_PATH, // Ensure the router is aware of the base path
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Return saved position when using back/forward buttons
    if (savedPosition) {
      return savedPosition;
    }
    // Scroll to top when navigating to a new route
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
        top: 100 // Offset for fixed header
      };
    }
    return { top: 0, behavior: 'smooth' };
  }
});

// Update page title and meta tags on route change
router.beforeEach((to, from, next) => {
  // Set the page title
  document.title = to.meta.title || 'CaseStrainer';
  
  // Remove any existing meta tags
  const existingMetaTags = document.querySelectorAll('meta[data-vue-router-controlled]');
  existingMetaTags.forEach(tag => tag.parentNode.removeChild(tag));
  
  // Add new meta tags
  if (to.meta.metaTags) {
    to.meta.metaTags.forEach(tag => {
      const metaTag = document.createElement('meta');
      Object.keys(tag).forEach(key => {
        metaTag.setAttribute(key, tag[key]);
      });
      metaTag.setAttribute('data-vue-router-controlled', '');
      document.head.appendChild(metaTag);
    });
  }
  
  next();
});

export default router;
