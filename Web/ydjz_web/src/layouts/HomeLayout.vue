<template>
  <div>
    <keep-alive  :include="cachedViews">

    <router-view  :key="key"  :include="cachedViews" style="margin-bottom: 60px">

    </router-view>
    </keep-alive>

    <van-tabbar route>
      <van-tabbar-item icon="balance-pay" to="/board">总览</van-tabbar-item>
      <van-tabbar-item icon="records" to="/flow">流水</van-tabbar-item>
      <van-tabbar-item icon="setting-o" to="/setting">设置</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script>
export default {

  // computed:{
  //   cachedViews(){
  //     return  this.$store.tagsView.cachedViews
  //   },
  //   key(){
  //     return this.$router.path
  //   }
  // },

  data() {
    return {
    };
  },
};
</script>

<style scoped>

</style>