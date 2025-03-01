<template>
  <div>
    <van-sticky>
      <van-nav-bar title="查找明细" left-arrow @click-left="onClickLeft" />
      <van-search
          v-model="note"
        shape="round"
        placeholder="请输入备注关键词"
        @search="onNoteSearch"
        show-action
    >
      <template #action>
        <div @click="onNoteSearch">搜索</div>
      </template>
    </van-search>
    <div style="height: 1px;width: 100%;background: #F7F8FA"/>
</van-sticky>
    <van-divider content-position="left" :style="{background:'#FFF', color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"> 选择日期 </van-divider>
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 0 16px;">
      <van-radio-group v-model="dateChoice" direction="horizontal" style="flex: 1;">
        <van-radio name="currentYear" @click="onDateChoice('currentYear')">当年</van-radio>
        <van-radio name="lastYear" @click="onDateChoice('lastYear')">上年</van-radio>
        <van-radio name="customMonth" @click="onDateChoice('customMonth')">选择月份</van-radio>
      </van-radio-group>
      <van-button v-if="dateChoice === 'customMonth'" type="default" round size="small" @click="showDatePicker = true" style="margin-left: 10px;">
        {{ showDate }}
      </van-button>
    </div>
    <van-divider content-position="left" :style="{background:'#FFF', color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"> 明细列表 </van-divider>
    <van-cell-group :border="false">
      <div @click="toUpdateFlow(flow.id, flow.handle)" v-for="flow in flows" :key="flow.id">
        <van-swipe-cell>
          <div style="
            margin-left: 15px;
            margin-top: 5px;
            font-size: 13px;
            color: #4e4e4e;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-right: 15px;
          ">
            <div>
              {{ flow.fdate }} <span style="color: #ccc;margin-left: 5px;">#{{ flow.id }}</span>
            </div>
            <van-icon name="link-o" color="#1989fa" style="font-size: 14px;"/>
          </div>
          <van-cell
              size="small"
              :title="flow.tname"
              :value="'￥' + flow.money"
              :label="flow.aname"
          >
            <template #label>
              <div>
                <label style="color: #676767; font-size: 13px; display: block;">{{ flow.aname }}</label>
                <label v-if="flow.note && flow.note.length>0"
                        style="color: #cea643; font-size: 13px; display: block; margin-top: 4px;">
                  {{ "备注：" + flow.note }}
                </label>
              </div>
            </template>
            <template #default>
              <div style="color: #000; font-size: 16px">￥{{ flow.money }}</div>
              <van-tag :type="flow.tagStyle">{{ flow.hname }}</van-tag>
              <van-tag
                  v-show="flow.exempt"
                  style="margin-left: 10px"
                  color="gray"
                  plain
                  type="action.style"
              >不计入总金额
              </van-tag>
            </template>
          </van-cell>
          <div style="height: 1px"></div>
        </van-swipe-cell>
      </div>
      <van-empty v-show="flows.length==0" description="暂无明细"/>
    </van-cell-group>
    <van-popup v-model:show="showDatePicker" close-on-click-overlay round position="bottom" :style="{height:'40%'}">
      <van-date-picker
          show-toolbar
          title="选择年月"
          type="year-month"
          v-model="currentChooseTime"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @cancel="showDatePicker = false"
          @confirm="onDateConfirm"
          :columns-type="columnsType"
      />
    </van-popup>
  </div>
</template>

<script>
export default {
  name: 'ScreenChoose',
  data() {
    return {
      columnsType: ["year", "month"],
      currentChooseTime: [new Date().getFullYear(), new Date().getMonth() + 1],
      showDatePicker: false,
      showDate:"",
      startDate: new Date().getFullYear() + "-01",//yyyy-MM
      endDate: new Date().getFullYear() + "-" + (new Date().getMonth() + 1), //yyyy-MM
      minDate: new Date(2021, 10, 1),
      maxDate: new Date(),
      dateChoice: 'currentYear',
      note: "",
      flows: [],
      totalIn: "",
      totalOut: "",
      totalEarn: "",
      singleMonth: true,
    };
  },
  mounted() {
    this.getFlowList();
  },
  methods: {
    formatter(type, option) {
      if (type === 'year') {
        option.text += '年';
      }
      if (type === 'month') {
        option.text += '月';
      }
      return option;
    },
    onClickLeft() {
      this.$router.go(-1);
    },
    onDateChoice(choice) {
      switch (choice) {
        case 'currentYear':
          this.startDate = new Date().getFullYear() + "-01-01";
          this.endDate = new Date().getFullYear() + "-12-31";
          this.singleMonth = false;
          break;
        case 'lastYear':
          this.startDate = new Date().getFullYear() - 1 + "-01-01";
          this.endDate = new Date().getFullYear() - 1 + "-12-31";
          this.singleMonth = false;
          break;
        case 'customMonth':
          this.showDate = new Date().getFullYear() + "-" + (new Date().getMonth() + 1).toString().padStart(2, "0");
          this.startDate = new Date().getFullYear() + "-" + (new Date().getMonth() + 1).toString().padStart(2, "0") + "-01";
          this.endDate = new Date().getFullYear() + "-" + (new Date().getMonth() + 1).toString().padStart(2, "0") + "-" + new Date().getDate();
          this.singleMonth = true;
          break;
      }
      console.log(this.startDate, this.endDate);
      this.getFlowList();
    },
    onDateConfirm({selectedValues}) {
      let pickDate = new Date(selectedValues[0], selectedValues[1] - 1);
      this.showDate = pickDate.getFullYear() + "-" + (pickDate.getMonth() + 1).toString().padStart(2, "0");
      this.startDate = pickDate.getFullYear() + "-" + (pickDate.getMonth() + 1).toString().padStart(2, "0") + "-01";
      this.endDate = pickDate.getFullYear() + "-" + (pickDate.getMonth() + 1).toString().padStart(2, "0") + "-" + new Date().getDate();
      this.showDatePicker = false;
      this.getFlowList();
    },

    onNoteSearch() {
      this.getFlowList();
    },

    getFlowList() {
      this.$http({
        url: "/screen/getFlowByScreen",
        method: "post",
        data: {
          accountId: -1,
          chooseHandle: 3, // 3表示全部
          startDate: this.startDate,
          endDate: this.endDate,
          singleMonth: this.singleMonth,
          collect: false,
          types: [],
          actions: [],
          note: this.note
        }
      }).then((response) => {
        console.log(response.data.data);
        const flow = response.data.data;
        this.flows = response.data.data.flows;
        this.totalIn = flow.totalIn;
        this.totalOut = flow.totalOut;
        this.totalEarn = flow.totalEarn;
        
        this.flows.forEach((flow) => {
          if (flow.handle === 0) {
            flow.handleName = "流入";
            flow.baseColor = "#4ae75a";
            flow.tagStyle = "success";
          } else if (flow.handle === 1) {
            flow.handleName = "流出";
            flow.tagStyle = "danger";
            flow.baseColor = "#f54949";
          } else if (flow.handle === 2) {
            flow.handleName = "内部转账";
            flow.tagStyle = "primary";
            flow.baseColor = "#39bdfa";
            flow.aname = flow.aname + "->" + flow.toAName
          }
          flow.dateSub = flow.fdate.substring(5, 10);
          flow.moneyNum = parseFloat(flow.money);
        });
      }).catch((error) => {
        console.log(error);
      });
    },

    toUpdateFlow(flowId, handle) {
      // 将所选明细信息存入localStorage，以便FlowAdd页面可以获取
      localStorage.setItem('selectedRelatedFlow', JSON.stringify({
        linkId: flowId,
        handle: handle
      }));
      console.log('数据已存入localStorage');
      // 返回上一页
      this.$router.go(-1);
    },
  }
}
</script>
<style scoped>
</style>

