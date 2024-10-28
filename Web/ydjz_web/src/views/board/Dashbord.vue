<template>
  <div>
    <van-nav-bar fixed placeholder title="总览" right-text="财务分析" @click-right=toAnalysis() />
    <div style="height: 40px;margin-left: 20px;margin-top:15px;font-size: 20px">总资产： ￥{{this.homeInfo.totalAsset}}</div>
    <div style="height: 30px;margin-left: 20px;font-size: 16px;color: #4e4e4e">净资产： ￥{{this.homeInfo.netAsset}}</div>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 当年收支情况
    </van-divider>
    <div style=" height:80px;background: #FFF;margin-left: 20px">
      <div style="margin-top: 10px; float: left">
        <div >本年总收入： <span style="color: #42b983">￥{{
            this.homeInfo.yearIncome
          }}</span></div>
        <div >本年总支出： <span style="color: #f54949">￥{{
            this.homeInfo.yearOutCome
          }}</span></div>
        <div >本年结余： ￥{{ this.homeInfo.yearBalance }}</div>
      </div>
    </div>
    <van-divider
      :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    >  账户资产
    </van-divider>
    <van-cell-group>
      <van-cell v-for="account in homeInfo.accounts" :key="account.id" :title="account.accountName"  size="large" :label="account.note"
                @click=toScreen(account.id)>
        <template #default>
          <div style="color: #000; font-size: 16px">￥{{account.accountAsset }}</div>
          <div style="color: #ccc; font-size: 14px">{{account.realAsset }}</div>

        </template>
        <template #title>
          <div style="color: #000; font-size: 19px">{{account.accountName }}</div>

        </template>
      </van-cell>
    </van-cell-group>

  </div>
</template>

<script>
import request from "../../utils/request";


export default {
  data() {
    return {
      money: 999,
      homeInfo:{},
    };
  },
  mounted() {
    this.getHomeInfo();
  },
  methods: {
    toAnalysis() {
      this.$router.push({ path: "/analysis" });
    },
    toScreen(acid) {
      this.$router.push({ path: "/screen", query: { acid: acid } });
    },
    getHomeInfo() {
      request({
        url: "/home/getHomeInfo",
        method: "get",
      }).then((resp) => {
        console.log(resp.data.data);
        this.homeInfo = resp.data.data
        this.homeInfo.accounts.map(account=>{
          if (account.exemptAsset!=''&&account.exemptAsset!=null){
            var fNum = parseFloat( account.accountAsset) - parseFloat(account.exemptAsset);
              account.realAsset ='净资产 ￥ '+( fNum.toFixed(2))
          }else {
            account.realAsset=='';
          }
        })
      });
    },
  },
};
</script>

<style scoped></style>
