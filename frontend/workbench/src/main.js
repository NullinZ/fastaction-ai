import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import FastActionView from './views/FastActionView.vue'
import FastActionTestView from './views/FastActionTestView.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/fastaction' },
    { path: '/fastaction', component: FastActionView },
    { path: '/fastaction/test', component: FastActionTestView }
  ]
})

createApp(App).use(router).mount('#app')

