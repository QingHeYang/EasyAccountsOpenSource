<template>
  <div id="app">
    <keep-alive :include="cacheComponents">
      <router-view></router-view>
    </keep-alive>
  </div>
</template>
<script>
export default {
  name: 'App',
  data() {
    return {
      cacheComponents: ['FlowAdd', 'ScreenChoose'] // 只缓存这些组件
    };
  },
  watch: {
    '$store.state.redirectToVerify': function (newValue) {
      if (newValue) {
        this.$router.push('/verify');
        this.$store.commit('setRedirectToVerify', false); // 重置状态，避免重复重定向
      }
    }
  }
};
</script>
<style lang="less">

</style>
