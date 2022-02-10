
const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/StreamViewer.vue') },
      { path: '/search', component: () => import('pages/Search.vue') },
      { path: '/generator', component: () => import('pages/Generator.vue')},
      { path: '/geosearch', component: () => import('pages/GeoSearch.vue')},
      { path: '/timeseries', component: () => import('pages/TimeSeries.vue')}
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/Error404.vue')
  }
]

export default routes
