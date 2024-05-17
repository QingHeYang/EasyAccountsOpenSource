import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import Vant from 'vant';
import 'vant/lib/index.css';
import axios from "axios";
//import VConsole from "vconsole/src/vconsole";
Vue.config.productionTip = false;
Vue.use(Vant)

axios.defaults.timeout = 5000 // 请求超时
//axios.defaults.baseURL = 'http://easy_accounts_net:10670/'
axios.defaults.baseURL = window.config.apiBaseUrl 

//new VConsole()
new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount("#app");
