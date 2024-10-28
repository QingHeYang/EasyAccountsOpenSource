<template>
  <div>
    <van-sticky :style="{background:'#FFFFFF'}">
    <van-nav-bar  fixed placeholder   title="流水" right-text="记一笔" @click-right=toAddFlow() />
    <van-dropdown-menu  active-color="#1989fa">
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
    </van-sticky>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 月度收支情况
    </van-divider>
    <div style=" height:80px;background: #FFF;margin-left: 20px">
      <div style="margin-top: 10px; float: left">
        <div v-show="this.totalIn!='0'">当月总收入： <span style="color: #42b983">￥{{
            this.totalIn
          }}</span></div>
        <div v-show="this.totalOut!='0'">当月总支出： <span style="color: #f54949">￥{{
            this.totalOut
          }}</span></div>
        <div v-show="this.handle===3">当月结余： ￥{{ this.totalEarn }}</div>
        <div v-show="this.handle===2">内部转账笔数： {{ this.flows.length }}</div>
      </div>
      <div style="display: flex; flex-direction: column; float: right;  margin-top: 5px; margin-right: 20px">
        <div style="display: flex; justify-content: space-around; align-items: center; width: 100%;">
          <van-button size="mini" plain type="info" icon="minus" @click="toLastMonth"></van-button>
          <van-button type="info" round size="small" plain style="margin-left: 5px; margin-right: 5px" icon="clock-o"
                      @click="()=>{showPicker = true}">
            {{ this.chooseMonth }}
          </van-button>
          <van-button size="mini" v-show="showNextMonthButton" plain type="info" icon="plus" @click="toNextMonth"></van-button>
        </div>
        <van-button  type="default" v-show="flows.length!=0" round size="small" style="margin-top: 10px;" @click="generateReport">生成报表</van-button>
      </div>

    </div>

    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 账本概览
    </van-divider>
    <van-cell-group :border="false">
      <div @click="toUpdateFlow(flow.id)" v-for="flow in flows" :key="flow.id">
        <van-swipe-cell >
          <template #left @open="()=>{currentFlow = flow}">
            <van-button size="small" square color="#8c8c8c" type="primary" class="delete-button"
                        @click="doShowNote(flow)">
              {{ doGetNotString(flow) }}
            </van-button>

          </template>
          <div style="
            margin-left: 15px;
            margin-top: 5px;
            font-size: 13px;
            color: #4e4e4e;
          ">
            {{ flow.fdate }}
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
            <van-button v-if="flow.collect" square type="warning" class="delete-button" @click="doCollectFlow(flow)">
              取消<br>收藏
            </van-button>
            <van-button v-else type="primary" color="#1989fa" class="delete-button" @click="doCollectFlow(flow)">收藏<br>账单
            </van-button>
            <van-button square text="删除" type="danger" class="delete-button" @click="doConfirmDeleteFlow(flow)"/>
          </template>
        </van-swipe-cell>
      </div>
    </van-cell-group>
    <van-empty v-show="flows.length==0" description="当月无账单" />


    <van-popup v-model="showPicker" round position="bottom">
      <van-datetime-picker
          show-toolbar
          title="选择年月"
          type="year-month"
          v-model="currentTime"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @cancel="showPicker = false"
          @confirm="this.onPickerClick"
      />
    </van-popup>

<!--    <button
        class="floating-button"
        :class="{'dragging': isDragging}"
        @touchstart="dragStart"
        @touchmove="dragMove"
        @touchend="dragEnd"
        ref="floatBtn"
    >
      +
    </button>-->
  </div>
</template>

<flow/>

<script>
import request from "../../utils/request";
import {Dialog, Toast} from 'vant';

export default {
  name: "Flow.vue",

  data() {
    return {
      initialX: 0,
      initialY: 0,
      isDragging: false,
      moved: false,
      showPicker: false,
      hasFlow: true,
      flowId: "",
      currentFlow: {},
      handle: 3,
      minDate: new Date(2021, 10),
      maxDate: new Date(),
      currentTime: new Date(),
      order: 0,
      option1: [
        {text: "总览", value: 3},
        {text: "只看流入", value: 0},
        {text: "只看流出", value: 1},
        {text: "只看内部转账", value: 2}
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
    };
  },

  mounted() {
    this.prepareDateDouble();
    this.chooseMonth = this.curDate.getFullYear() + "-" + (this.curDate.getMonth() + 1).toString().padStart(2, "0");
    this.getMonthFlow();
    //document.addEventListener('touchmove', this.dragMove);
  },
  methods: {
    /*dragStart(event) {
      this.moved = false;
      const touch = event.touches[0];
      this.initialX = touch.clientX;
      this.initialY = touch.clientY;
      this.offsetX = touch.clientX - (this.$refs.floatBtn.offsetLeft + this.$refs.floatBtn.offsetWidth / 2);
      this.offsetY = touch.clientY - (this.$refs.floatBtn.offsetTop + this.$refs.floatBtn.offsetHeight / 2);
      document.addEventListener('touchmove', this.dragMove, { passive: false });
      document.addEventListener('touchend', this.dragEnd);
    },
    dragMove(event) {
      if (!this.moved) {
        const touch = event.touches[0];
        const deltaX = Math.abs(touch.clientX - this.initialX);
        const deltaY = Math.abs(touch.clientY - this.initialY);
        if (deltaX > 5 || deltaY > 5) {
          this.moved = true;
          this.isDragging = true;
        }
      }
      if (this.moved) {
        event.preventDefault(); // 防止默认的滚动行为
        const touch = event.touches[0];

        // 根据偏移量计算新的位置
        const newX = touch.clientX - this.offsetX - this.$refs.floatBtn.offsetWidth / 2;
        const newY = touch.clientY - this.offsetY - this.$refs.floatBtn.offsetHeight / 2;

        // 边界检测
        const finalX = Math.max(0, Math.min(newX, window.innerWidth - this.$refs.floatBtn.offsetWidth));
        const finalY = Math.max(100, Math.min(newY, window.innerHeight - this.$refs.floatBtn.offsetHeight - 100));

        // 更新悬浮球位置
        this.$refs.floatBtn.style.left = `${finalX}px`;
        this.$refs.floatBtn.style.top = `${finalY}px`;
      }
    },
    dragEnd(event) {
      if (this.moved) {
        event.preventDefault();
      } else {
        this.handleClick();
      }
      this.isDragging = false;
      document.removeEventListener('touchmove', this.dragMove);
      document.removeEventListener('touchend', this.dragEnd);
    },
    handleClick() {
      if (!this.isDragging) {
        this.toAddFlow();
      }
    },*/
    formatter(type, val) {
      if (type === 'year') {
        return `${val}年`;
      }
      if (type === 'month') {
        return `${val}月`;
      }
      return val;
    },


    getMonthFlow() {
      request({
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
    toUpdateFlow(flowId) {
      this.$router.push({path: "/flow/add", query: {flowId: flowId}});
    },

    doConfirmDeleteFlow(flow) {
      console.log(this.flow)
      Dialog.confirm({
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
      request({
        url: "/flow/deleteFlow/" + this.flowId,
        method: "delete"
      }).then(() => {
        this.getMonthFlow();
      });
    },

    doCollectFlow(flow) {
      console.log("/flow/collectFlow/" + flow.id + "/" + (flow.collect ? 0 : 1))
      request({
        url: "/flow/collectFlow/" + flow.id + "/" + (flow.collect ? 0 : 1),
        method: "put"
      }).then(() => {
        this.getMonthFlow();
      });
    },

    doShowNote(flow) {
      if (flow.note != null&&flow.note.length>4) {
        Dialog.alert({
          title: '备注',
          message: flow.note,
        }).then(() => {
          // on close
        });
      }
    },

    doGetNotString(flow){
      if (flow.note==null||flow.note==""){
        return "无备注"
      }else if (flow.note.length>4){
        return flow.note.substring(0,3)+".."
      }else {
        return flow.note
      }
    },

    prepareDateDouble() {

    },
    onPickerClick(value) {
      console.log(new Date(value));
      this.chooseMonth = value.getFullYear() + "-" + (value.getMonth() + 1).toString().padStart(2, "0");
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
        this.getMonthFlow(); // 更新数据
      }else {
        Toast.fail("已经到最后了")
      }
    },

    generateReport() {
      //this.$router.push({path: "/flow/report", query: {month: this.chooseMonth}});
      Dialog.confirm({
        title: '确定生成报表吗？',
        message:
            '确定生成 ' +this.chooseMonth + " 月度报表吗？",
      })
          .then(() => {
            this.makeExcel()
          })
          .catch(() => {
            // on cancel
          });
    },
    makeExcel(){
      request({
        url: "/flow/makeExcel/" + this.chooseMonth,
        method: "get"
      }).then(() => {
        this.getMonthFlow();
      });
    }

  },

};
</script>

<style scoped>
.delete-button {
  height: 100%;
  white-space: pre-wrap;
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
