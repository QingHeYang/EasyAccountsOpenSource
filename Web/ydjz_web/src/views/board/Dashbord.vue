<template>
  <div>
    <!--    <van-nav-bar fixed placeholder title="总览" right-text="财务分析" @click-right=toAnalysis() />-->
    <van-nav-bar
        title="总览"/>
    <div
        style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background-color: #fff; border-bottom: 1px solid #ececec;">
      <div>
        <div style="font-size: 20px; font-weight: 600; color: #333;">总资产：￥{{ this.homeInfo.totalAsset }}</div>
        <div style="font-size: 16px; color: #333; margin-top: 5px;">净资产：￥{{ this.homeInfo.netAsset }}</div>
      </div>
      <van-button
          type="default"
          round
          size="small"
          style="margin-top: 5px; margin-left: 20px; font-size: 14px; color: #333; border: 1px solid #ececec;"
          @click="showAccountsDetail=true"
      >
        账户详情
      </van-button>
    </div>


    <div style=" height:100px;background: #FFF; border-bottom: 1px solid #ececec;padding: 15px 20px;">
      <div style="margin-top: 10px; float: left">
        <div style="margin-bottom: 5px;">
          年度总收入： <span style="color: #42b983">￥{{ this.homeInfo.yearIncome }}</span>
        </div>
        <div style="margin-bottom: 5px;">
          年度总支出： <span style="color: #f54949">￥{{ this.homeInfo.yearOutCome }}</span>
        </div>
        <div>
          年度结余： ￥{{ this.homeInfo.yearBalance }}
        </div>
      </div>
      <div style="display: flex; flex-direction: column; float: right;  margin-top: 5px; ">
        <div style="display: flex; justify-content: space-around; align-items: center; width: 100%;">
          <van-button size="mini" plain type="primary" icon="minus" @click="toLastYear"></van-button>
          <van-button type="primary" round size="small" plain style="margin-left: 5px; margin-right: 5px" icon="clock-o"
                      @click="()=>{showYearPicker = true}">
            {{ this.chooseYear }}
          </van-button>
          <van-button size="mini" plain type="primary" icon="plus"
                      @click="toNetYear"></van-button>
        </div>
      </div>
    </div>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > {{ this.chooseYear }}年月度概览
    </van-divider>
    <van-cell-group style="margin-left: 10px;margin-right: 10px">
      <!-- 表头 -->
      <van-row
          style="
      padding: 10px 20px;
      background-color: #fbfbfb;
      border-bottom: 1px solid #ececec;
    "
          type="flex"
          justify="space-between"
      >
        <van-col span="3" style="font-weight: bold; color: #333;justify-content: center">月份</van-col>
        <van-col span="7" style="font-weight: bold; color: #333;justify-content: center">收入</van-col>
        <van-col span="7" style="font-weight: bold; color: #333;">支出</van-col>
        <van-col span="7" style="font-weight: bold; color: #333;">结余</van-col>
      </van-row>

      <!-- 数据行 -->
      <div v-if="homeInfo.monthDetails!=null&&homeInfo.monthDetails.length>0">
        <div v-for="month in homeInfo.monthDetails" :key="month.month" @click="toFlow(month.month)">
          <van-row style="padding: 10px 20px;font-size: 14px;color: #555;border-bottom: 1px solid #ececec;" type="flex"
                   justify="space-between"
          >
            <van-col span="3">{{ month.month }}月</van-col>
            <van-col span="7" style="color: #42b983">￥{{ month.income }}</van-col>
            <van-col span="7" style="color: #f54949">￥{{ month.outcome }}</van-col>
            <van-col span="7">￥{{ month.balance }}</van-col>
          </van-row>
        </div>
      </div>
      <van-empty v-else description="暂无数据"/>
    </van-cell-group>


    <van-popup v-model:show="showYearPicker" round position="bottom">
      <van-picker
          show-toolbar
          title="选择年份"
          :columns="yearList"
          @cancel="showYearPicker = false"
          @confirm="this.onPickerChoose"
      />
    </van-popup>
    <van-action-sheet v-model:show="showAccountsDetail" round position="bottom" title="账户概览">
      <van-cell-group>
        <van-cell
            v-for="account in homeInfo.accounts"
            :key="account.id"
            :title="account.accountName"
            size="large"
            :label="account.note"
            @click="toScreen(account.id)"
            style="padding: 12px 20px; border-bottom: 1px solid #ececec;"
        >
          <template #default>
            <div style="color: #333; font-size: 16px; font-weight: 600;">￥{{ account.accountAsset }}</div>
            <div style="color: #999; font-size: 14px;">{{ account.realAsset }}</div>
          </template>
          <template #title>
            <div style="color: #333; font-size: 18px; font-weight: 600; margin-bottom: 5px;">{{
                account.accountName
              }}
            </div>
          </template>
        </van-cell>
      </van-cell-group>

    </van-action-sheet>

  </div>
</template>

<script>


import {showFailToast} from "vant";

export default {
  data() {
    return {
      money: 999,
      chooseYear: new Date().getFullYear(),
      minYear: 2021,
      yearList: [],
      showYearPicker: false,
      showNextYearButton: false,
      showAccountsDetail: false,
      homeInfo: {},
    };
  },
  mounted() {
    this.getHomeInfo();
    this.prepareYearColum();
  },
  methods: {
    prepareYearColum() {
      var year = new Date().getFullYear();
      for (var i = year; i >= this.minYear; i--) {
        this.yearList.push({text: i + '年', value: i});
      }
    },

    toLastYear() {
      if (this.chooseYear === this.minYear) {
        showFailToast('已经到最前了');
        return
      }
      this.chooseYear = this.chooseYear - 1;
      this.controlNextYearButton()
      this.getHomeInfo();
    },

    toNetYear() {
      if (this.chooseYear === new Date().getFullYear()) {
        showFailToast('已经到最后了');
        return
      }
      this.chooseYear = this.chooseYear + 1;
      this.controlNextYearButton()
      this.getHomeInfo();
    },

    onPickerChoose({selectedValues}) {
      if (selectedValues[0] === this.chooseYear) {
        this.showYearPicker = false;
        return;
      }
      this.chooseYear = selectedValues[0];

      this.showYearPicker = false;
      this.controlNextYearButton()

      this.getHomeInfo()
    },

    controlNextYearButton() {
      var year = new Date().getFullYear();
      if (this.chooseYear < year) {
        this.showNextYearButton = true;
      } else {
        this.showNextYearButton = false;
      }
    },

    toAnalysis() {
      this.$router.push({path: "/analysis"});
    },
    toScreen(acid) {
      this.$router.push({path: "/screen", query: {acid: acid}});
    },

    toFlow(month) {
      var str = this.chooseYear + '-' + month.toString().padStart(2, "0");
      console.log(str);
      this.$router.push({path: "/flow", query: {month: str, key: Date.now()}});
    },

    getHomeInfo() {
      this.$http({
        url: "/home/getHomeInfoV2/" + this.chooseYear,
        method: "get",
      }).then((resp) => {
        console.log(resp.data.data);
        this.homeInfo = resp.data.data
        this.homeInfo.accounts.map(account => {
          if (account.exemptAsset != '' && account.exemptAsset != null) {
            var fNum = parseFloat(account.accountAsset) - parseFloat(account.exemptAsset);
            account.realAsset = '净资产 ￥ ' + (fNum.toFixed(2))
          } else {
            account.realAsset == '';
          }
        })
      }).catch((error) => {
        console.error("获取首页信息失败:", error);
      });
    },
  },
};
</script>

<style scoped></style>
