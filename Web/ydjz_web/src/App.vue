<template>
  <div id="app">
  <router-view :key="$route.fullPath"></router-view>
  </div>
</template>
<script>
export default {
  name: 'App',
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
