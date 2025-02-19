<template>
  <div>
    <van-nav-bar
        title="单项分类统计"
        left-text="返回"
        left-arrow
        @click-left="onClickLeft"
    />
    <div style=" height:70px;background: #FFF; border-bottom: 1px solid #ececec;padding: 15px 20px;">
      <div style="margin-top: 10px; float: left">
        <div style="margin-bottom: 5px;">
          分类： {{ this.chooseType.tname == null ? '请选择分类' : this.chooseType.tname }}
          <van-tag v-if="this.chooseType.tname!=null&&this.chooseType.action!=null"
                   :type="this.chooseType.action.handle === 0 ? 'success' : 'danger'"
                   size="medium" style="margin-left: 5px;">{{ this.chooseType.action.hname }}
          </van-tag>
        </div>
        <div style="margin-bottom: 5px;" v-show="typeData.totalIncome!=null && typeData.totalIncome!='0.00'">
          分类收入： <span style="color: #42b983">￥{{ this.typeData.totalIncome }}</span>
        </div>
        <div v-show="typeData.totalOutcome!=null && typeData.totalOutcome!='0.00'">
          分类支出： <span style="color: #f54949">￥{{ this.typeData.totalOutcome }}</span>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; float: right;  margin-top: 5px; ">
        <div style="display: flex; justify-content: space-around; align-items: start; width: 100%;">
          <van-button type="default" round size="small" @click="()=>{showTypeSheet=true}">选择分类</van-button>
        </div>
      </div>
    </div>

    <div style="background: #FFFFFF; padding: 15px;">
      <van-radio-group
          v-model="fastChoose"
          direction="horizontal"
          style="display: flex; flex-wrap: wrap; gap: 10px;"
      >
        <van-radio name="1" @click="onFastDateChoose(fastChoose)">近一年</van-radio>
        <van-radio name="2" @click="onFastDateChoose(fastChoose)">今年</van-radio>
        <van-radio name="3" @click="onFastDateChoose(fastChoose)">上年</van-radio>
        <van-radio name="4" @click="onFastDateChoose(fastChoose)">自定义</van-radio>
      </van-radio-group>
      <div v-show="fastChoose == 4" style="display: flex; align-items: center; margin-top: 15px;">
        <span style="font-size: 16px; color: #333; margin-right: 8px;">选择时间段</span>
        <van-button
            type="default"
            round
            size="small"
            @click="()=>{showPicker = true}"
            icon="clock-o"
            style="padding: 0 10px;"
        >
          {{ setTimeButton() }}
        </van-button>
      </div>
    </div>


    <van-empty v-if="this.typeData.typeId==null||this.typeData.yearData.length==0" description="暂无数据"/>
    <div v-else v-for="yearItem in typeData.yearData" :key="yearItem.year">
      <!-- 年份信息 -->
      <van-cell-group style="margin-left: 5px">

        <van-cell
            :title="yearItem.year + ' 年'"
        >
          <template #value>
            <span v-if="yearItem.income!=null && yearItem.income!='0.00'"
                  style="color: #42b983">年收入： ￥{{ yearItem.income }}</span>
            <span v-if="yearItem.outcome!=null && yearItem.outcome!='0.00'"
                  style="color: #f54949"> 年支出￥{{ yearItem.outcome }}</span>
          </template>
        </van-cell>
      </van-cell-group>
      <!-- 月份数据 -->
      <van-cell-group v-for="monthItem in yearItem.monthData" style="margin-left: 15px;"
                      :key="monthItem.month">
        <van-cell
            @click="()=>{getTypeFlows(0,yearItem.year+'-'+monthItem.month.toString().padStart(2, '0'));showFlowList = true}"
            v-if="monthItem.income!=null && monthItem.income!='0.00'"
            :title="yearItem.year + '年' + monthItem.month + '月'"
            :value="'收入：￥' + monthItem.income ">
          <template #value>
            <span style="color: #42b983">￥{{ monthItem.income }}</span>
          </template>
        </van-cell>
        <van-cell
            @click="()=>{getTypeFlows(1,yearItem.year+'-'+monthItem.month.toString().padStart(2, '0'));showFlowList = true}"
            v-if="monthItem.outcome!=null && monthItem.outcome!='0.00'"
            :title="yearItem.year + '年' + monthItem.month + '月'"
            :value="' 支出：￥' + monthItem.outcome">
          <template #value>
            <span style="color: #f54949">￥{{ monthItem.outcome }}</span>
          </template>
        </van-cell>

      </van-cell-group>
    </div>
    <van-popup round v-model:show="showPicker" position="bottom">

      <van-picker-group
          title="选择时间段"
          :tabs="['开始日期', '结束日期']"
          @confirm="onConfirm"
          @cancel="onCancel"
      >
        <van-date-picker
            v-model="chooseStartTime"
            :min-date="minDate"
            :max-date="maxDate"
            :formatter="formatter"
            :columns-type="columnsType"
        />
        <van-date-picker
            v-model="chooseEndTime"
            :min-date="minDate"
            :max-date="maxDate"
            :formatter="formatter"
            :columns-type="columnsType"
        />
      </van-picker-group>
    </van-popup>

    <van-popup round v-model:show="showTypeSheet" position="bottom">
      <van-cascader
          v-model="typeId"
          title="选择账单分类"
          :options="treeAllTypes"
          active-color="#1989fa"
          @close="showTypeSheet = false"
          :field-names="cascaderNames"
          @finish="onChooseCascader"
      />
    </van-popup>

    <van-action-sheet round v-model:show="showFlowList" position="bottom" :title="this.clickTitle" style="height: 60%">
      <van-cell-group :border="false">
        <div v-for="flow in flows" :key="flow.id">
          <van-swipe-cell>

            <div style="
            margin-left: 15px;
            margin-top: 5px;
            font-size: 11px;
            color: #4e4e4e;">
              {{ flow.fdate }}
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
                  <label v-if="flow.note.length>0"
                         style="color: #cea643; font-size: 13px; display: block; margin-top: 4px;">{{
                      "备注：" + flow.note
                    }}</label>
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
      </van-cell-group>
    </van-action-sheet>
  </div>
</template>

<script>
import {showToast} from "vant";

export default {
  name: "AnalysisType",
  data() {
    return {
      showPicker: false,
      showTypeSheet: false,
      showFlowList: false,

      columnsType: ["year", "month"],
      startDate: new Date().getFullYear() - 1 + "-" + (new Date().getMonth() + 1),//yyyy-MM
      endDate: new Date().getFullYear() + "-" + (new Date().getMonth() + 1), //yyyy-MM
      currentDate: new Date(),

      currentTime: [new Date().getFullYear(), new Date().getMonth() + 1],
      chooseStartTime: [new Date().getFullYear() - 1, new Date().getMonth() + 1],
      chooseEndTime: [new Date().getFullYear(), new Date().getMonth() + 1],
      minDate: new Date(2021, 10, 1),
      maxDate: new Date(),

      fastChoose: "1",

      typeId: "",
      typeName: "",
      chooseType: {},
      types: [],
      typeData: {},
      treeAllTypes: [],
      cascaderNames: {
        text: 'tname',
        value: 'id',
        children: 'childrenTypes',
      },

      flows: [],
      clickTitle: "",
    };
  },
  mounted() {
    this.typeId = this.$route.query.typeId;
    this.getAllTypes();
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

    setTimeButton() {
      return this.formatDate(this.startDate) + " 至 " + this.formatDate(this.endDate);
    },

    onConfirm() {
      if (this.chooseStartTime[0] > this.chooseEndTime[0] ||
          (this.chooseStartTime[0] === this.chooseEndTime[0] && this.chooseStartTime[1] > this.chooseEndTime[1])) {
        showToast("开始时间不能大于结束时间");
        return;
      }


      this.startDate = this.chooseStartTime[0] + "-" + this.chooseStartTime[1];
      this.endDate = this.chooseEndTime[0] + "-" + this.chooseEndTime[1];
      this.showPicker = false;
      this.getTypeData();
    },

    onCancel() {
      console.log("onCancel");
      this.showPicker = false;
    },

    formatDate(date) {
      const year = date.split("-")[0];
      const month = date.split("-")[1].padStart(2, "0");
      return year + "年" + month + "月";
    },

    onClickLeft() {
      this.$router.go(-1);
    },

    getTypeData() {
      if (!this.chooseType.id) {
        return;
      }
      this.$http({
        url: "/analysis/v2/getAnalysisTypeMonthData",
        method: "post",
        data: {
          typeId: this.chooseType.id,
          start: this.startDate,
          end: this.endDate,
        },
      })
          .then((response) => {
            this.typeData = response.data.data;
            console.log(this.typeData);
          })
    },

    getAllTypes() {
      this.$http({
        url: "/type/getType",
        method: "get",
      })
          .then((response) => {
            this.types = response.data.data;
            this.setAllTypes(this.types)
            if (this.typeId) {
              this.chooseType = this.findTypeById(this.types, this.typeId);
              if (this.chooseType) {
                this.getTypeData();
              }
              console.log(this.chooseType);
            }
          })
    },

    /*{
      "singleMonth": true,
        "accountId": -1,
        "note": "",
        "types": [67],
        "endDate": "",
        "chooseHandle": 0,
        "actions": [],
        "collect": false,
        "startDate": "2025-02-04"
    }
    {
        "singleMonth": true,
        "accountId": 0,
        "note": "",
        "types": [67],
        "endDate": "",
        "chooseHandle": 0,
        "actions": [],
        "collect": false,
        "startDate": "2025-02-01"
    }
    */

    getTypeFlows(chooseHandel, date) {
      this.clickTitle = date.substring(0, 4) + "年" + date.substring(5, 7) + "月";
      var startDate = date + "-01";
      this.$http({
        url: "/screen/getFlowByScreen",
        method: "post",
        data: {
          accountId: -1,
          chooseHandle: chooseHandel,
          startDate: startDate,
          endDate: "",
          singleMonth: true,
          collect: false,
          types: [this.chooseType.id],
          actions: null,
          note: ""
        }
      }).then((response) => {
        this.flows = response.data.data.flows;
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
          if (this.handle === 3) {
            this.detail = this.chooseMonth + "总收入： ￥" + this.totalIn + "  总支出： ￥" + this.totalOut;
          }
          flow.dateSub = flow.fdate.substring(5, 10);
          flow.moneyNum = parseFloat(flow.money);
        });
        console.log(this.typeData);
      })
    },


    setAllTypes(data) {
      const allTypes = data;
      allTypes.forEach((item) => {
        item.text = item.tname
        if (item.childrenTypes != null) {
          const chileTypes = item.childrenTypes;
          chileTypes.unshift({
            tname: "选择当前一级分类",
            tOriginName: item.tname,
            id: item.id,
            parent: item.parent
          })
          chileTypes.forEach((children) => {
            children.text = children.tname
          })
        }
        item.children = item.childrenTypes
      })
      this.treeAllTypes = allTypes
    },

    onChooseCascader() {
      this.showTypeSheet = false;
      this.chooseType = this.findTypeById(this.types, parseInt(this.typeId));
      this.getTypeData();
    },

    findTypeById(types, typeId) {
      var findId = parseInt(typeId);
      for (let item of types) {
        if (item.id === findId) {
          return item;
        }
        // 如果有子分类，则递归查找
        if (item.childrenTypes && item.childrenTypes.length > 0) {
          const found = this.findTypeById(item.childrenTypes, findId);
          if (found) {

            found.tname = item.tname + "/" + found.tname;
            return found;
          }
        }
      }
      return null;
    },

    onFastDateChoose(fastChoose) {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth();

      switch (fastChoose) {
        case "1":
          this.startDate = `${year - 1}-${month + 1}`;
          this.endDate = `${year}-${month + 1}`;
          break;
        case "2":
          this.startDate = `${year}-01`;
          this.endDate = `${year}-${month + 1}`;
          break;
        case "3":
          this.startDate = `${year - 1}-01`;
          this.endDate = `${year - 1}-12`;
          break;
      }
      this.startDate = this.startDate.replace(/-(\d)$/, "-0$1");
      this.endDate = this.endDate.replace(/-(\d)$/, "-0$1");
      this.chooseStartTime = this.startDate.split("-");
      this.chooseEndTime = this.endDate.split("-");
      console.log(this.startDate, this.endDate);
      if (fastChoose !== "4") {
        this.getTypeData();
      }
    }
  },
};
</script>

<style>

</style>