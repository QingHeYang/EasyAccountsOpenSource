<template>
  <div>
    <!-- 开启顶部安全区适配 -->
    <keep-alive >
      <router-view   style="margin-bottom: 80px">
      </router-view>
    </keep-alive>

    <van-tabbar  route style="padding-bottom: 20px">
      <van-tabbar-item icon="balance-pay" to="/board">总览</van-tabbar-item>
      <van-tabbar-item icon="records" to="/flow">流水</van-tabbar-item>
      <van-tabbar-item icon="filter-o" to="/screen">筛选</van-tabbar-item>
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
      key:""
    };
  },
};
</script>

<style scoped>

</style>