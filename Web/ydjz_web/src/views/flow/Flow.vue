<template>
  <div>
    <van-nav-bar fixed placeholder title="明细" right-text="筛选" @click-right=toScreen() />
    <van-floating-bubble icon="plus" axis="xy" magnetic="x" v-model:offset="offset" @click="toAddFlow"/>
    <van-dropdown-menu active-color="#1989fa">
      <van-dropdown-item
          v-model="handle"
          :options="option1"
          @change="onHandleClick"
      />
      <van-dropdown-item
          v-model="order"
          :options="option2"
          @change="onHandleClick"
      />
    </van-dropdown-menu>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 月度收支情况
    </van-divider>
    <div style=" height:80px;background: #FFF;margin-left: 20px">
      <div style="margin-top: 10px; float: left">
        <div v-show="this.totalIn!='0'">当月总收入： <span style="color: #42b983">￥{{ this.totalIn }}</span></div>
        <div v-show="this.totalOut!='0'">当月总支出： <span style="color: #f54949">￥{{ this.totalOut }}</span></div>
        <div v-show="this.handle===3">当月结余： ￥{{ this.totalEarn }}</div>
        <div v-show="this.handle===2">内部转账笔数： {{ this.flows.length }}</div>
      </div>
      <div style="display: flex; flex-direction: column; float: right;  margin-top: 5px; margin-right: 20px">
        <div style="display: flex; justify-content: space-around; align-items: center; width: 100%;">
          <van-button size="mini" plain type="primary" icon="minus" @click="toLastMonth"></van-button>
          <van-button type="primary" round size="small" plain style="margin-left: 5px; margin-right: 5px" icon="clock-o"
                      @click="()=>{showPicker = true}">
            {{ this.chooseMonth }}
          </van-button>
          <van-button size="mini" v-show="showNextMonthButton" plain type="primary" icon="plus"
                      @click="toNextMonth"></van-button>
        </div>
        <van-button type="default" v-show="flows.length!=0" round size="small" style="margin-top: 10px;"
                    @click="generateReport">生成报表
        </van-button>
      </div>

    </div>

    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 账本概览
    </van-divider>

    <van-cell-group :border="false">
      <div @click="toUpdateFlow(flow.id)" v-for="flow in flows" :key="flow.id">
        <van-swipe-cell>
          <!--          <template #left @open="handleOpen">-->
          <template #left>
            <van-button size="small" square color="#8c8c8c" type="success" class="delete-button"
                        @click="doShowNote(flow)">
              {{ doGetNotString(flow) }}
            </van-button>

          </template>
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
            <van-icon name="link-o" color="#1989fa" style=" font-size: 14px;"/>
          </div>
          
          <van-cell
              size="large"
              :title="flow.tname"
              :value="'￥' + flow.money"
              :label="flow.aname"
          >
            <template #default>
              <div style="color: #000; font-size: 19px">￥{{ flow.money }}</div>
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

          <template #right>
            <div style="display: flex;  align-items: center; height: 100%;">
              <!-- 文字需要在最中间，纵向也居中 -->
              <div 
                v-if="flow.collect" 
                style="background-color: #ffc107; cursor: pointer; color: #fff;
                height: 100%; font-size: 14px;width: 60px; text-align: center;
                display: flex;align-items: center;justify-content: center;" 
                @click="doCollectFlow(flow)"
              >
                取消<br>收藏
              </div>
              <div 
                v-else 
                style="background-color: #1989fa; cursor: pointer; 
                color: #fff;height: 100%; font-size: 14px;width: 60px; text-align: 
                center;display: flex;align-items: center;justify-content: center;" 
                @click="doCollectFlow(flow)"
              >
                收藏<br>账单
              </div>
              <div 
                style="background-color: #28a745;color: #fff;height: 100%; 
                font-size: 14px;width: 60px; text-align: center;
                display: flex;align-items: center;justify-content: center;" 
              >
                查看<br>关联
              </div>
            </div>
          </template>
        </van-swipe-cell>
      </div>
    </van-cell-group>
    <van-empty v-show="flows.length==0" description="当月无账单"/>


    <van-popup v-model:show="showPicker" round position="bottom">
      <van-date-picker
          show-toolbar
          title="选择年月"
          type="year-month"
          v-model="currentChooseTime"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @cancel="showPicker = false"
          @confirm="this.onPickerClick"
          :columns-type="columnsType"
      />
    </van-popup>
  </div>
</template>


<script>
import {closeToast, showConfirmDialog, showDialog, showFailToast, showLoadingToast} from 'vant';

export default {
  name: "Flow.vue",

  data() {
    return {
      columnsType: ["year", "month"],
      initialX: 0,
      initialY: 0,
      isDragging: false,
      moved: false,
      showPicker: false,
      hasFlow: true,
      flowId: "",
      currentFlow: {},
      handle: 3,
      minDate: new Date(2021, 10, 1),
      maxDate: new Date(),
      currentChooseTime: [new Date().getFullYear(), new Date().getMonth() + 1],
      order: 0,
      option1: [
        {text: "全部", value: 3},
        {text: "资金流入", value: 0},
        {text: "资金流出", value: 1},
        {text: "内部转账", value: 2}
      ],
      option2: [
        {text: "按时间排序", value: 0},
        {text: "按金额排序", value: 1}
      ],
      flows: [],
      totalIn: "",
      totalOut: "",
      totalEarn: "",
      detail: "",
      showNextMonthButton: true,
      chooseMonth: "",
      curDate: new Date(),
      editShow: false,
      actions: [{name: "编辑", color: "#39bdfa"}, {name: "删除", color: "#f54949"}],
      columns: [
        // 第一列
      ],
      offsetX: 0,
      offsetY: 0,
      offset: {x: 0, y: 0},
    };
  },

  mounted() {
    this.prepareDateDouble();
    this.chooseMonth = this.curDate.getFullYear() + "-" + (this.curDate.getMonth() + 1).toString().padStart(2, "0");
    this.getMonthFlow();
    //document.addEventListener('touchmove', this.dragMove);
    this.offset = {x: window.innerWidth - 83, y: window.innerHeight - 180};
    localStorage.removeItem('selectedRelatedFlow');
  },
  watch: {
    '$route': 'handleRouteChange'
  },
  methods: {

    handleRouteChange() {
      const newMonth = this.$route.query.month;
      if (newMonth !== this.chooseMonth) {
        this.chooseMonth = newMonth || this.curDate.getFullYear() + "-" + (this.curDate.getMonth() + 1).toString().padStart(2, "0");
        this.getMonthFlow();
      }
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


    getMonthFlow() {
      this.$http({
        url:
            "/flow/getFlowListMain/" +
            this.handle +
            "/" +
            this.order +
            "/" +
            this.chooseMonth,
        method: "get"
      }).then((response) => {
        console.log(response.data.data);
        const flow = response.data.data;
        this.flows = response.data.data.flows;
        this.totalIn = flow.totalIn;
        this.totalOut = flow.totalOut;
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
          }
          if (this.handle === 3) {
            this.detail = this.chooseMonth + "总收入： ￥" + this.totalIn + "  总支出： ￥" + this.totalOut;
          }
          flow.dateSub = flow.fdate.substring(5, 10);
          flow.moneyNum = parseFloat(flow.money);
        });
        var fEarn = parseFloat(this.totalIn) - parseFloat(this.totalOut);

        this.totalEarn = fEarn.toFixed(2)
      });
    },
    onHandleClick() {
      this.getMonthFlow();
    },
    toAddFlow() {
      this.$router.push({path: "/flow/add"});
    },

    toScreen() {
      this.$router.push({path: "/screen"});
    },

    toUpdateFlow(flowId) {
      this.$router.push({path: "/flow/add", query: {flowId: flowId}});
    },

    doConfirmDeleteFlow(flow) {
      console.log(this.flow)
      showConfirmDialog({
        title: '确定删除吗？',
        message:
            '确定删除 ￥' + flow.money + " 的  '" + flow.tname + "'  记录吗？",
      })
          .then(() => {
            this.flowId = flow.id
            this.doDeleteFlow()
          })
          .catch(() => {
            // on cancel
          });

    },

    doDeleteFlow() {
      this.$http({
        url: "/flow/deleteFlow/" + this.flowId,
        method: "delete"
      }).then(() => {
        this.getMonthFlow();
      });
    },

    doCollectFlow(flow) {
      console.log("/flow/collectFlow/" + flow.id + "/" + (flow.collect ? 0 : 1))
      this.$http({
        url: "/flow/collectFlow/" + flow.id + "/" + (flow.collect ? 0 : 1),
        method: "put"
      }).then(() => {
        this.getMonthFlow();
      });
    },

    doShowNote(flow) {
      if (flow.note != null && flow.note.length > 4) {
        showDialog({
          title: '备注',
          message: flow.note,
        }).then(() => {
          // on close
        });
      }
    },

    doGetNotString(flow) {
      if (flow.note == null || flow.note == "") {
        return "无备注"
      } else if (flow.note.length > 4) {
        return flow.note.substring(0, 3) + ".."
      } else {
        return flow.note
      }
    },

    prepareDateDouble() {

    },
    onPickerClick({selectedValues}) {
      let pickDate = new Date(selectedValues[0], selectedValues[1] - 1);
      console.log(new Date(selectedValues[0], selectedValues[1] - 1));
      this.chooseMonth = pickDate.getFullYear() + "-" + (pickDate.getMonth() + 1).toString().padStart(2, "0");
      this.getMonthFlow()
      this.showPicker = false;
    },

    toLastMonth() {
      let parts = this.chooseMonth.split("-");
      let year = parseInt(parts[0]);
      let month = parseInt(parts[1]);

      if (month === 1) {
        this.chooseMonth = (year - 1) + "-12";
      } else {
        this.chooseMonth = year + "-" + (month - 1).toString().padStart(2, "0");
      }

      this.currentChooseTime = [this.chooseMonth.split("-")[0], this.chooseMonth.split("-")[1]];
      this.getMonthFlow(); // 假设这个方法用来获取指定月份的数据
    },


    toNextMonth() {
      let parts = this.chooseMonth.split("-");
      let year = parseInt(parts[0]);
      let month = parseInt(parts[1]);
      let currentYear = this.curDate.getFullYear();
      let currentMonth = this.curDate.getMonth() + 1; // JavaScript的getMonth()从0开始计数

      if (year < currentYear || (year === currentYear && month < currentMonth)) {
        if (month === 12) {
          this.chooseMonth = (year + 1) + "-01";
        } else {
          this.chooseMonth = year + "-" + (month + 1).toString().padStart(2, "0");
        }
        this.currentChooseTime = [year, month + 1];
        this.getMonthFlow(); // 更新数据
      } else {
        showFailToast("已经到最后了")
      }
    },

    generateReport() {
      //this.$router.push({path: "/flow/report", query: {month: this.chooseMonth}});
      showConfirmDialog({
        title: '确定生成报表吗？',
        message:
            '确定生成 ' + this.chooseMonth + " 月度报表吗？",
      })
          .then(() => {
            this.makeExcel()
          })
          .catch(() => {

          });
    },
    makeExcel() {
      showLoadingToast({
        message: '生成中...',
        forbidClick: true,
      });
      this.$http({
        url: "/flow/makeExcel/" + this.chooseMonth,
        method: "get"
      }).then((resp) => {
        // {
        //   "code": 0,
        //     "msg": "Success",
        //     "data": {
        //   "success": true,
        //       "log": "文件生成成功\n调用webhook成功\n月度 Excel 发送功能已关闭"
        //
        // }
        var excelresult = resp.data.data;
        var title = excelresult.success?'成功':'失败';
        closeToast();
        showDialog({
          title: '报表生成'+title,
          message: excelresult.log,
          cancelButtonText: '确定',
        })
      })
    }
  },

};
</script>

<style scoped>
.delete-button {
  height: 100%;
  white-space: pre-wrap;
  width: 65px;
}

.note {
  height: 100%;
  font-size: 11px;
  width: 80px;
  text-align: center;
  padding-top: 30px;
  padding-left: 10px;
  background: #9e9e9e;
  word-wrap: break-word;
  color: #FFFFFF;
  line-height: 100%;
  white-space: pre-wrap;
}

.floating-button {
  position: fixed;
  right: 15px;
  bottom: 100px;
  width: 50px;
  height: 50px;
  font-size: 24px; /* 调整字体大小确保+号看起来居中 */
  color: white;
  background-color: #57BD6A; /* 基础绿色 */
  border-radius: 50%;
  cursor: pointer;
  border: none;
  outline: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: background-color 0.3s, box-shadow 0.3s, transform 0.3s;
  display: flex; /* 使用flex布局 */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  text-align: center; /* 确保文本居中 */
  line-height: 50px; /* 增加行高以垂直居中文字 */
  transform: scale(1); /* 初始缩放比例 */
}


.floating-button:hover, .floating-button.dragging {
  background-color: #419a54; /* 交互时的更深绿色 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); /* 增强的阴影 */
  transform: scale(1.05); /* 轻微放大 */
}

.floating-button:active {
  background-color: #57BD6A; /* 点击时恢复到基础绿色 */
  transform: scale(1); /* 恢复原始大小 */
}

</style>
