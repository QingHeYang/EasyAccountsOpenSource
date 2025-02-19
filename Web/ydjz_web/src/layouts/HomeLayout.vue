<template>
  <van-config-provider :theme="dark">
    <div>
      <!-- 开启顶部安全区适配 -->
      <keep-alive>
        <router-view style="margin-bottom: 80px">
        </router-view>
      </keep-alive>

      <van-tabbar route style="padding-bottom: 20px">
        <van-tabbar-item icon="balance-pay" to="/board">总览</van-tabbar-item>
        <van-tabbar-item icon="records-o" to="/flow">明细</van-tabbar-item>
        <van-tabbar-item icon="chart-trending-o" to="/analysisV2">统计</van-tabbar-item>
<!--        <van-tabbar-item icon="filter-o" to="/screen">筛选</van-tabbar-item>-->
        <van-tabbar-item icon="setting-o" to="/setting">设置</van-tabbar-item>
      </van-tabbar>


    </div>
  </van-config-provider>
</template>

<script>
export default {

  data() {
    return {
      key: "",
      offset :{x: 20, y: 100 }
    };
  },
  mounted() {
    //设置到屏幕右下角
    this.offset = {x: window.innerWidth-80, y: window.innerHeight - 140};
  },
  methods: {
    toAddFlow() {
      this.$router.push({path: "/flow/add"});
    },
  },
};
</script>

<style scoped>

</style>