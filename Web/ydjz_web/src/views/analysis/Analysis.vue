<template>
  <div class="analysis">
    <van-nav-bar title="财务分析"  left-arrow   @click-left="onClickLeft"/>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 条件选择
    </van-divider>
    <van-space direction="horizontal">
      <van-radio-group v-model="fastChoose" style="padding-left: 15px;flex-wrap: wrap" direction="horizontal">
        <van-radio name=0 @click="onFastDateChoose(fastChoose)">当月</van-radio>
        <van-radio name=1 @click="onFastDateChoose(fastChoose)">上月</van-radio>
        <van-radio name=2 @click="onFastDateChoose(fastChoose)">全年</van-radio>
        <van-radio name=3 @click="onFastDateChoose(fastChoose)">上年</van-radio>
        <van-radio name=4 @click="onFastDateChoose(fastChoose)">自定义</van-radio>
      </van-radio-group>
    </van-space>
    <div style="padding-left: 15px;padding-right: 15px;padding-top: 10px">
      <!-- 日期选择区域 -->
      <div style="display: flex; justify-content: left; align-items: center; margin-bottom: 10px;"
           v-show="fastChoose==4">
        <!-- 开始日期组 -->
        <div style="display: flex; align-items: center; margin-right: 20px;">
          <span style="margin-right: 10px; font-size: 14px;">开始：</span>
          <van-button type="default" round size="small" icon="clock-o" @click="()=>{showStartPicker = true}">
            {{ startChooseMonth }}
          </van-button>
        </div>
        <!-- 结束日期组 -->
        <div style="display: flex; align-items: center;">
          <span style="margin-right: 10px; font-size: 14px;">结束：</span>
          <van-button type="default" round size="small" icon="clock-o" @click="()=>{showEndPicker = true}">
            {{ endChooseMonth }}
          </van-button>
        </div>
      </div>

      <!-- 按钮区域 -->
      <div style="display: flex; justify-content: space-around; margin-bottom: 10px;">
        <van-button type="default" round size="small" style="flex: 1; margin-right: 10px;" @click="generateReport">
          生成当期报表
        </van-button>
        <van-button type="default" round size="small" style="flex: 1;" @click="query" v-show="fastChoose==4">
          查询
        </van-button>
      </div>
    </div>
    <div >
      <van-divider
          :style="{ color: '#11759e', borderColor: '#11759e', padding: '0 16px' }" content-position="left"
      > 同比周期
      </van-divider>

      <div v-if="this.yoyList.length!==0">
        <div style="margin-left: 15px">
          <div class="period-info">
            <label class="period-label">本周期：</label><span>{{ currentCircle }}</span>
          </div>
          <div class="period-info">
            <label class="period-label">同比周期：</label><span>{{ yoyCircle }}</span>
          </div>
        </div>
        <div v-if="yoyList.length !== 0">
          <van-row class="row">
            <van-col span="6" class="col">
              <div class="item" style="background-color: #0b688e;">
                <label>分类</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #0289ba;">
                <label>周期金额</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #40b0d8;">
                <label>同比金额</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #4ac0ea;">
                <label>同比增量</label>
              </div>
            </van-col>
            <van-col span="3" class="col">
              <div class="item" style="background-color: #a7def6;">
                <label>增速</label>
              </div>
            </van-col>
          </van-row>
        </div>
        <div>
          <van-row class="row" v-for="type in yoyList" :key="type.id">
            <van-col span="6" class="col">
              <div class="item" style="background-color: #11759e;">
                <label>{{ type.name }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #0289ba;">
                <label>{{ type.money }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #0093C4;">
                <label>{{ type.compareMoney }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #4ac0ea;">
                <label>{{ type.compareIncrease }}</label>
              </div>
            </van-col>
            <van-col span="3" class="col">
              <div class="item" style="background-color: #a7def6;">
                <label>{{ type.compareRate }}</label>
              </div>
            </van-col>
          </van-row>
        </div>
      </div>
    </div>
    <van-empty v-show="this.yoyList.length===0" description="周期内无同比"/>
    <div>
      <van-divider
          :style="{ color: '#096858', borderColor: '#096858', padding: '0 16px' }" content-position="left"
      > 环比周期
      </van-divider>

      <div v-if="this.momList.length!==0">
        <div style="margin-left: 15px">
          <div class="period-info">
            <label class="period-label">本周期：</label><span>{{ currentCircle }}</span>
          </div>
          <div class="period-info">
            <label class="period-label">环比周期：</label><span>{{ momCircle }}</span>
          </div>
        </div>
        <div v-if="momList.length !== 0">
          <van-row class="row">
            <van-col span="6" class="col">
              <div class="item" style="background-color: #096858;">
                <label>分类</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #06887a;">
                <label>周期金额</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #26A69A;">
                <label>环比金额</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #51cdc2;">
                <label>环比增量</label>
              </div>
            </van-col>
            <van-col span="3" class="col">
              <div class="item" style="background-color: #9deae3;">
                <label>增速</label>
              </div>
            </van-col>
          </van-row>
        </div>
        <div style="margin-bottom: 40px">
          <van-row class="row" v-for="type in momList" :key="type.id">
            <van-col span="6" class="col">
              <div class="item" style="background-color: #096858;">
                <label>{{ type.name }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #06887a;">
                <label>{{ type.money }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #26A69A;">
                <label>{{ type.compareMoney }}</label>
              </div>
            </van-col>
            <van-col span="5" class="col">
              <div class="item" style="background-color: #51cdc2;">
                <label>{{ type.compareIncrease }}</label>
              </div>
            </van-col>
            <van-col span="3" class="col">
              <div class="item" style="background-color: #9deae3;">
                <label>{{ type.compareRate }}</label>
              </div>
            </van-col>
          </van-row>
        </div>
      </div>
      <van-empty v-show="this.momList.length===0" description="周期内无环比"/>
    </div>


    <van-popup v-model="showStartPicker" round position="bottom">
      <van-datetime-picker
          show-toolbar
          title="选择开始年月"
          type="year-month"
          v-model="currentTime"
          :min-date="startMinDate"
          :max-date="startMaxDate"
          :formatter="formatter"
          @cancel="showStartPicker = false"
          @confirm="this.onStartPickerClick"
      />
    </van-popup>

    <van-popup v-model="showEndPicker" round position="bottom">
      <van-datetime-picker
          show-toolbar
          title="选择结束年月"
          type="year-month"
          v-model="currentTime"
          :min-date="endMinDate"
          :max-date="endMaxDate"
          :formatter="formatter"
          @cancel="showEndPicker = false"
          @confirm="this.onEndPickerClick"
      />
    </van-popup>
  </div>
</template>

<script>
import {Dialog, Toast} from "vant";
import request from "../../utils/request";

export default {
  name: "Analysis",
  data() {
    return {
      fastChoose: '0',
      startChooseMonth: '',
      endChooseMonth: '',
      showStartPicker: false,
      showEndPicker: false,
      anadata: null,
      yoyList: [],
      momList: [],
      yoyCircle: "",
      momCircle: "",
      currentCircle: "",
      currentTime: new Date(),
      startMinDate: new Date(2021, 11, 1),
      startMaxDate: new Date(),
      endMinDate: new Date(2021, 11, 1),
      endMaxDate: new Date(),
      initialStartMinDate: new Date(2021, 11, 1),
      initialStartMaxDate: new Date(),
      initialEndMinDate: new Date(2021, 11, 1),
      initialEndMaxDate: new Date(),
    }
  },

  mounted() {

    this.startChooseMonth = this.currentTime.getFullYear() + "-" + (this.currentTime.getMonth() + 1).toString().padStart(2, "0");
    this.query();
  },

  methods: {
    onClickLeft() {
      this.$router.go(-1);
    },
    formatter(type, val) {
      if (type === 'year') {
        return `${val}年`;
      }
      if (type === 'month') {
        return `${val}月`;
      }
      return val;
    },

    onFastDateChoose(value) {
      console.log(value);
      let year = this.currentTime.getFullYear();
      let month = this.currentTime.getMonth() + 1; // JavaScript的月份是从0开始的，所以需要+1

      if (value === '0') {
        this.startChooseMonth = `${year}-${month.toString().padStart(2, "0")}`;
        this.endChooseMonth = "";
        this.query();
      } else if (value === '1') {
        if (month === 1) { // 如果当前是1月，则上个月是上一年的12月
          year -= 1;
          month = 12;
        } else {
          month -= 1; // 否则，只需月份减1
        }
        this.startChooseMonth = `${year}-${month.toString().padStart(2, "0")}`;
        this.endChooseMonth = "";
        this.query();
      } else if (value === '2') {
        this.startChooseMonth = `${year}-01`;
        this.endChooseMonth = `${year}-${month.toString().padStart(2, "0")}`;
        this.query();
      } else if (value === '3') {
        year -= 1; // 上一年
        this.startChooseMonth = `${year}-01`;
        this.endChooseMonth = `${year}-12`;
        this.query();
      } else if (value === '4') {
        this.startChooseMonth = "";
        this.endChooseMonth = "";
        this.startMinDate = this.initialStartMinDate;
        this.startMaxDate = this.initialStartMaxDate;
        this.endMinDate = this.initialEndMinDate;
        this.endMaxDate = this.initialEndMaxDate;
        this.yoyList=[]
        this.momList=[]
      }
    },

    generateReport() {
      //this.$router.push({path: "/flow/report", query: {month: this.chooseMonth}});
      Dialog.confirm({
        title: '确定生成报表吗？',
        message:
            '确定生成 ' +this.startChooseMonth + " 财务分析表吗？",
      })
          .then(() => {
            this.makeExcel()
          })
          .catch(() => {
            // on cancel
          });
    },

    makeExcel(){
      if (this.startChooseMonth === "" && this.endChooseMonth === "") {
        Toast.fail('开始日期和结束日期至少选择一个');
        return;
      }
      let startQueryStr = ""
      let endQueryStr = ""
      if (this.startChooseMonth === "" && this.endChooseMonth !== "") {
        startQueryStr = this.endChooseMonth;
        endQueryStr = ""
      } else {
        startQueryStr = this.startChooseMonth;
        endQueryStr = this.endChooseMonth;
      }
      request({
        url:
            "/analysis/exportExcel?start=" +
            startQueryStr +
            "&end=" +
            endQueryStr,
        method: "get"
      }).then(() => {
        this.query();
      });
    },

    query() {
      if (this.startChooseMonth === "" && this.endChooseMonth === "") {
        Toast.fail('开始日期和结束日期至少选择一个');
        return;
      }
      let startQueryStr = ""
      let endQueryStr = ""
      if (this.startChooseMonth === "" && this.endChooseMonth !== "") {
        startQueryStr = this.endChooseMonth;
        endQueryStr = ""
      } else {
        startQueryStr = this.startChooseMonth;
        endQueryStr = this.endChooseMonth;
      }

      request({
        url:
            "/analysis/doAnalysis?start=" +
            startQueryStr +
            "&end=" +
            endQueryStr,
        method: "get"
      }).then((resp) => {
        console.log(resp.data.data);
        this.anadata = resp.data.data;
        this.yoyList = this.anadata.yoyList;
        if (this.yoyList.length !== 0) {
          this.yoyCircle;
        }
        this.momList = this.anadata.momList;
        this.yoyCircle = this.anadata.yoyCircle;
        this.momCircle = this.anadata.momCircle;
        this.currentCircle = this.anadata.currentCircle;
      });
    },

    onStartPickerClick(value) {
      const selectedDate = new Date(value);
      console.log(selectedDate);
      this.startChooseMonth = selectedDate.getFullYear() + "-" + (selectedDate.getMonth() + 1).toString().padStart(2, "0");
      this.showStartPicker = false;

      // 更新结束日期选择器的最小日期为选中的开始日期的当月第一天
      this.endMinDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);

      // 更新结束日期选择器的最大日期为当前年份的12月，或者选中的开始日期的当年当月（如果开始时间是今年）
      const currentYear = new Date().getFullYear();
      const endMaxMonth = selectedDate.getFullYear() === currentYear ? new Date().getMonth() : 11;
      this.endMaxDate = new Date(selectedDate.getFullYear(), endMaxMonth, new Date(selectedDate.getFullYear(), endMaxMonth + 1, 0).getDate());
    },

    onEndPickerClick(value) {
      const selectedDate = new Date(value);
      console.log(selectedDate);
      this.endChooseMonth = selectedDate.getFullYear() + "-" + (selectedDate.getMonth() + 1).toString().padStart(2, "0");
      this.showEndPicker = false;

      // 更新开始日期选择器的最小日期为选中的结束日期的当年1月
      this.startMinDate = new Date(selectedDate.getFullYear(), 0, 1);

      // 更新开始日期选择器的最大日期为选中的结束日期的当年当月
      this.startMaxDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0).getDate());
    },

  }
}
</script>

<style scoped>
.row {
  display: flex;
  margin-left: 10px;
  margin-right: 10px;
  flex-wrap: nowrap; /* Keep columns on the same line */
}

.col {
  display: flex;
  flex-direction: column;
  justify-content: stretch;
}

.item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1px;
  margin-bottom: 1px;
  padding: 5px;
  font-size: 12px;
  color: #fff;
}

/* 设置第二个及以后的列文字颜色为黑色 */
.col:nth-child(n + 4) .item {
  color: #333;
}

.col:nth-child(n+5) .item {
  font-size: 10px;
}

.period-info {
  display: flex;
  align-items: center;
}

.period-label {
  margin-right: 5px;
  font-weight: bold;
}

.period-info span {
  color: #333;
}
</style>