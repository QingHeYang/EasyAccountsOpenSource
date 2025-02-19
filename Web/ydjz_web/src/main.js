import { createApp } from 'vue'; // 使用 Vue 3 的 API
import App from './App.vue';
import router from './router';
import store from './store';
import Vant from 'vant';
import 'vant/lib/index.css';
import request from './axios'; // 引入 Axios
import VueApexCharts from "vue3-apexcharts";
import { ConfigProvider } from 'vant';

// 不需要 Vue.config.productionTip = false 和 Vue.use(Vant)
const app = createApp(App);

// 使用 Vant 和其它插件
app.use(store).use(router).use(Vant).use(VueApexCharts).use(ConfigProvider);

// 将 $http 挂载到 Vue 3 实例
app.config.globalProperties.$http = request;

// 挂载应用
app.mount('#app');
