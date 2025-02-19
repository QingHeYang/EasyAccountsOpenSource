import { createStore } from 'vuex';  // 使用 Vuex 4 的创建 store 的方法

export default createStore({
  state: {
    redirectToVerify: false,
  },
  mutations: {
    setRedirectToVerify(state, value) {
      state.redirectToVerify = value;
    },
  },
  actions: {},
  modules: {},
});
