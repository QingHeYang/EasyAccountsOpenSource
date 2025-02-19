<template>
  <div>
    <van-nav-bar fixed placeholder title="分类统计" right-text="单项分类" @clickRight="onRightClick"/>
    <div style=" height:85px;background: #FFF; border-bottom: 1px solid #ececec;padding: 15px 20px;">
      <div style="margin-top: 10px; float: left">
        <div style="margin-bottom: 5px;">
          开始时间： <span style="color: #333">{{ this.formatTime(this.startDate) }}</span>
        </div>
        <div style="margin-bottom: 5px;">
          结束时间： <span style="color: #333">{{ this.formatTime(this.endDate) }}</span>
        </div>
        <div>
          总计： <span :style="{ color: renderThemeColor }">￥{{ this.showTotal }}</span>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; float: right;  margin-top: 5px; ">
        <div style="display: flex; justify-content: space-around; align-items: center; width: 100%;">
          <van-button type="primary" round size="small" plain  @click="()=>{showDatePicker = true}">
            统计条件
          </van-button>
        </div>
        <van-button  type="default" round size="small" style="margin-top: 10px;" @click="showCharts=true">查看图表</van-button>
      </div>
    </div>

    <van-tabs v-model:active="tabIndex" swipeable type="card" :color="this.renderThemeColor"
              @click-tab="this.onTabClick" style="margin-top: 15px">
      <van-tab v-for="item in this.tabOptions" :title="item.title" :key="item.index">

        <van-cell-group style="margin-top: 15px">
          <van-cell v-for="item in this.useTypeList" :key="item.id" :title="item.name " :value="'￥'+item.money" @click="toAnalysisType(item.id)">
            <template #title>
              <span style="font-size: 16px; color: #333;">{{ item.name }}</span>
            </template>

            <template #value>
              <span style="font-size: 16px; color: #3c3c3c;margin-right: 10px">￥{{ item.money }}</span>
              <van-tag type="success" :color="renderThemeColor"  size="large">{{ item.percent+'%' }}</van-tag>
            </template>
          </van-cell>
        </van-cell-group>

      </van-tab>

    </van-tabs>
    <van-action-sheet v-model:show="showDatePicker" round position="bottom" title="统计条件">
      <div>
        <van-divider
            content-position="left"
            :style="{background:'#FFF', color: '#1989fa', borderColor: '#1989fa', padding: '0 10px' }"
        > 选择参数
        </van-divider>
        <van-checkbox-group v-model="modelChoose"
                            style="background: #FFFFFF; display: flex; flex-wrap: wrap; justify-content: center; padding-left: 15px;padding-right: 15px">
          <van-checkbox shape="square" name="0" @click="onModelChange(modelChoose)" style="flex: 1 0 22%; margin: 5px;">
            合并子分类
          </van-checkbox>
          <van-checkbox shape="square" name="1" @click="onModelChange(modelChoose)" style="flex: 1 0 22%; margin: 5px;">
            显示全部分类
          </van-checkbox>
        </van-checkbox-group>
        <van-divider
            content-position="left"
            :style="{background:'#FFF', color: '#1989fa', borderColor: '#1989fa', padding: '0 10px' }"
        > 选择时间
        </van-divider>
        <van-radio-group v-model="fastChoose"
                         style="background: #FFFFFF; display: flex; flex-wrap: wrap; justify-content: center; padding-left: 15px;padding-right: 15px">
          <van-radio name="0" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">当月</van-radio>
          <van-radio name="1" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">上月</van-radio>
          <van-radio name="2" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">近3月
          </van-radio>
          <van-radio name="3" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">近6月
          </van-radio>
          <van-radio name="4" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">近1年
          </van-radio>
          <van-radio name="5" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">当年</van-radio>
          <van-radio name="6" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">上年</van-radio>
          <van-radio name="7" @click="onFastDateChoose(fastChoose)" style="flex: 1 0 22%; margin: 5px;">自定义
          </van-radio>
        </van-radio-group>
        <div v-show="fastChoose==7"
             style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;padding-left: 15px;padding-right: 15px;margin-top: 10px">
          <!-- 开始日期组 -->
          <div style="display: flex; align-items: center; width: 48%; justify-content: flex-start;">
            <span style="margin-right: 10px; font-size: 14px;">开始：</span>
            <van-button type="default" round size="small" icon="clock-o" @click="()=>{showStartPicker = true}"
                        style="flex-grow: 1; text-align: center;">
              {{ startDate }}
            </van-button>
          </div>

          <!-- 结束日期组 -->
          <div style="display: flex; align-items: center; width: 48%; justify-content: flex-start;">
            <span style="margin-right: 10px; font-size: 14px;">结束：</span>
            <van-button type="default" round size="small" icon="clock-o" @click="()=>{showEndPicker = true}"
                        style="flex-grow: 1; text-align: center;">
              {{ endDate }}
            </van-button>
          </div>
        </div>

        <van-button square style="width: 100%; margin-top: 10px; margin-left: auto; margin-right: auto;" type="primary"
                    size="large" @click="this.onConfirmBtnClick">
          确定
        </van-button>

      </div>
    </van-action-sheet>

    <van-popup v-model:show="showStartPicker" round position="bottom">
      <van-date-picker
          show-toolbar
          title="选择开始年月"
          v-model="currentTime"
          :min-date="startMinDate"
          :max-date="startMaxDate"
          :formatter="formatter"
          @cancel="showStartPicker = false"
          @confirm="this.onStartPickerClick"
          :columns-type="columnsType"
      />
    </van-popup>

    <van-popup v-model:show="showEndPicker" round position="bottom">
      <van-date-picker
          show-toolbar
          title="选择结束年月"
          v-model="currentTime"
          :min-date="endMinDate"
          :max-date="endMaxDate"
          :formatter="formatter"
          @cancel="showEndPicker = false"
          @confirm="this.onEndPickerClick"
          :columns-type="columnsType"
      />
    </van-popup>

    <van-popup v-model:show="showCharts" position="top" :style="{ width: '100%' ,background:'#F7F8FA' }">
      <van-nav-bar fixed placeholder title="查看图表">
        <template #right>
          <van-icon name="cross" size="18" @click="()=>{showCharts = false}"/>
        </template>
      </van-nav-bar>
      <ApexChart  type="treemap" :options="treeChartOptions" :series="treeseries" style="margin-top: 20px;margin-left: 10px;margin-right: 10px;margin-bottom: 20px"></ApexChart>
<!--      <ApexChart type="donut" :options="donutChartOptions" :series="donutseries" style="margin-top: 20px"></ApexChart>-->
    </van-popup>
  </div>
</template>
<script>
import ApexCharts from 'vue3-apexcharts';
import {showToast} from "vant";

export default {
  name: "AnalysisV2",
  components: {
    ApexChart: ApexCharts,
  },

  mounted() {
    this.onAnalysisV2Request();
    this.renderThemeColor = this.inThemeColor;
  },
  data() {
    return {
      tabIndex: 0,

      tabOptions: [
        {title: "收入", index: 0},
        {title: "支出", index: 1},
      ],

      formatTime(date) {
        const year = date.split("-")[0];
        const month = date.split("-")[1].padStart(2, "0");
        return year + "年" + month + "月";
      },

      columnsType: ["year", "month"],
      startDate: new Date().getFullYear() + "-" + (new Date().getMonth() + 1),//yyyy-MM
      endDate: new Date().getFullYear() + "-" + (new Date().getMonth() + 1), //yyyy-MM
      fastChoose: "0",
      modelChoose: ['1'],
      showDatePicker: false,
      combineSubType: false,
      showDisableAnalysisType: true,
      showStartPicker: false,
      showEndPicker: false,
      showCharts: false,

      currentTime: [new Date().getFullYear(), new Date().getMonth() + 1],
      startMinDate: new Date(2021, 10, 1),
      startMaxDate: new Date(),
      endMinDate: new Date(2021, 10, 1),
      endMaxDate: new Date(),

      donutseries: [],
      donutChartOptions: {},
      treeseries: [],
      treeChartOptions:{},
      inThemeColor: "#11941f",
      outThemeColor: "#c23737",
      renderThemeColor: "",

      totalIn: "",
      totalOut: "",
      showTotal: "",
      totalTitle: "",
      showInTypeList: [],
      showOutTypeList: [],
      allInTypeList: [],
      allOutTypeList: [],

      useTypeList: [],
    };
  },

  methods: {
    onRightClick() {
      this.$router.push({path: "/analysis/type"});
    },

    toAnalysisType(typeId) {
      this.$router.push({path: "/analysis/type" ,query:{typeId: typeId}});
    },

    onTabClick({title}) {
      console.log(title);
      if (title === "支出") {
        this.renderThemeColor = this.outThemeColor;
      } else {
        this.renderThemeColor = this.inThemeColor;
      }
      this.onAnalysisV2Request();
    },

    onChooseData() {
      this.showCharts = true;
    },

    formatter(type, option) {
      if (type === 'year') {
        option.text += '年';
      }
      if (type === 'month') {
        option.text += '月';
      }
      return option;
    },

    onFastDateChoose(fastChoose) {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth();

      switch (fastChoose) {
        case "0", "7": { // 当月
          this.startDate = `${year}-${month + 1}`;
          this.endDate = `${year}-${month + 1}`;
          break;
        }
        case "1": { // 上月
          const startMonth = month === 0 ? 12 : month;
          const yearOffset = month === 0 ? year - 1 : year;
          this.startDate = `${yearOffset}-${startMonth}`;
          this.endDate = `${yearOffset}-${startMonth}`;
          break;
        }
        case "2": { // 近3月
          const startMonth = month - 2 < 0 ? 12 + (month - 2) : month - 2;
          const yearOffset = month - 2 < 0 ? year - 1 : year;
          this.startDate = `${yearOffset}-${startMonth + 1}`;
          this.endDate = `${year}-${month + 1}`;
          break;
        }
        case "3": { // 近6月
          const startMonth = month - 5 < 0 ? 12 + (month - 5) : month - 5;
          const yearOffset = month - 5 < 0 ? year - 1 : year;
          this.startDate = `${yearOffset}-${startMonth + 1}`;
          this.endDate = `${year}-${month + 1}`;
          break;
        }
        case "4": { // 近1年
          this.startDate = `${year - 1}-${month + 1}`;
          this.endDate = `${year}-${month + 1}`;
          break;
        }
        case "5": { // 当年
          this.startDate = `${year}-01`;
          this.endDate = `${year}-${month + 1}`;
          break;
        }
        case "6": { // 上年
          this.startDate = `${year - 1}-01`;
          this.endDate = `${year - 1}-12`;
          break;
        }
      }
      this.startDate = this.startDate.replace(/-(\d)$/, "-0$1");
      this.endDate = this.endDate.replace(/-(\d)$/, "-0$1");
    },

    onModelChange(value) {
      if (value.includes("0")) {
        this.combineSubType = true;
      } else {
        this.combineSubType = false;
      }
      if (value.includes("1")) {
        this.showDisableAnalysisType = true;
      } else {
        this.showDisableAnalysisType = false;
      }
    },

    onStartPickerClick({selectedValues}) {
      const selectedDate = new Date(selectedValues[0], selectedValues[1] - 1);
      const endData = new Date(this.endDate);
      if (endData < selectedDate) {
        showToast("开始日期不能大于结束日期");
        return;
      }
      this.startDate = selectedDate.getFullYear() + "-" + (selectedDate.getMonth() + 1).toString().padStart(2, "0");
      this.showStartPicker = false;
    },

    onEndPickerClick({selectedValues}) {
      const selectedDate = new Date(selectedValues[0], selectedValues[1] - 1);
      const startData = new Date(this.startDate);
      if (startData > selectedDate) {
        showToast("结束日期不能小于开始日期");
        return;
      }
      this.endDate = selectedDate.getFullYear() + "-" + (selectedDate.getMonth() + 1).toString().padStart(2, "0");
      this.showEndPicker = false;
    },

    onConfirmBtnClick() {
      this.showDatePicker = false;
      this.onAnalysisV2Request();
    },

    onAnalysisV2Request() {
      this.$http({
        url: "/analysis/v2/getAnalysisTypeList",
        method: "post",
        data: {
          start: this.startDate,
          end: this.endDate,
          combineSubType: this.combineSubType,
          showDisableAnalysisType: this.showDisableAnalysisType,
        },
      }).then((res) => {
        this.totalIn = res.data.data.totalIn;
        this.totalOut = res.data.data.totalOut;
        this.showInTypeList = res.data.data.showInTypeList;
        this.showOutTypeList = res.data.data.showOutTypeList;
        this.allInTypeList = res.data.data.allInTypeList;
        this.allOutTypeList = res.data.data.allOutTypeList;
        this.renderChart();
      });
    },

    renderChart() {
      if (this.tabIndex === 0) {
        this.showTotal = this.totalIn;
        this.totalTitle = "收入总计";
        this.useTypeList = this.allInTypeList;
        this.makeTreeChartOptions(this.showInTypeList);
        this.makeDonutChartOptions(this.showInTypeList);
      } else {
        this.showTotal = this.totalOut;
        this.totalTitle = "支出总计";
        this.useTypeList = this.allOutTypeList;
        this.makeTreeChartOptions(this.showOutTypeList);
        this.makeDonutChartOptions(this.showOutTypeList);
      }
    },

    makeTreeChartOptions(data) {
      //数据格式：[ data: {name: 'xxx', money: 'xxx'}]

      // 转换数据格式为目标格式
      this.treeseries = [
        {
          data: data.map(item => ({
            x: item.name+"\n"+`(${item.percent}%)`,
            y: parseFloat(item.money) || 0
          }))
        }
      ];
      console.log(this.treeseries);
      this.treeChartOptions = {
        chart: {
          type: 'treemap',
          width: '100%',
          height: '500',
        },
        plotOptions: {
          treemap: {
            enableShades: true
          }
        },
        theme: {
          monochrome: {
            enabled: true,
            color: this.renderThemeColor,
            shadeIntensity: 1,
            shadeTo: 'light',
          },
        },
        legend: {
          show: true,
          position: 'bottom',
          horizontalAlign: 'center',
        },

        title: {
          text: this.tabIndex === 0 ? "收入分类" : "支出分类",
        }
      };
    },

    makeDonutChartOptions(data) {
      this.donutseries = data.map(item => parseFloat(item.money));
      this.donutChartOptions = {
        chart: {
          type: 'donut',
          width: '400',
          height: '300',
        },
        plotOptions: {
          pie: {
            donut: {
              size: '75%', // 设置 Donut 的大小
              labels: {
                show: true,  // 显示总计标签
                total: {
                  show: true,  // 显示总计
                  label: this.totalTitle,  // 总计标签
                  fontSize: '14px',  // 字体大小
                  fontFamily: 'Helvetica, Arial, sans-serif',  // 字体
                  color: '#333',  // 颜色
                  formatter: () => {
                    return this.showTotal; // 计算总计
                  }
                }
              }
            }
          }
        },
        legend: {
          show: true,
          position: 'bottom',  // 将图例移到底部
          horizontalAlign: 'center',  // 水平居中
          itemsPerRow: 1,  // 每行显示 2 个图例
        },

        /*        responsive: [{
                  breakpoint: 300,
                  options: {
                    chart: {
                      height: '400',
                    },
                    legend: {
                      position: 'bottom',
                      horizontalAlign: 'center',
                    },
                  }
                }],*/
        labels: data.map(item => item.name),
        theme: {
          monochrome: {
            enabled: true,
            color: this.renderThemeColor,
            shadeIntensity: 1,
            shadeTo: 'light',
          },
        },
        // 增加 dataLabels 配置项
        dataLabels: {
          enabled: true, // 是否启用数据标签
          formatter: (val) => {
            return val.toFixed(1) + '%';  // 显示百分比
          },
          style: {
            fontSize: '11px',
            fontFamily: 'Helvetica, Arial, sans-serif',
            fontWeight: 'bold',
            colors: ['#fff']  // 数据标签的颜色
          }
        }
      };

    }

  }
};
</script>

<style scoped>

</style>