<template>
  <div>
    <!--  1.8版本 筛选功能  -->
    <van-sticky :style="{background:'#FFFFFF'}">
      <van-nav-bar fixed placeholder title="筛选" left-text="备注筛选" right-text="更多条件"
                   @click-right="()=>{morePopupShow=true}"
                   @click-left="onClickLeft"/>
      <!--   备注搜索 2.1.0版本   -->
      <van-search
          v-if="useNote"
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

    <van-divider
        content-position="left"
        :style="{background:'#FFF', color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 快速切换
    </van-divider>
    <van-radio-group v-model="fastChoose" style="background:#FFFFFF; padding-left: 15px;flex-wrap: wrap"
                     direction="horizontal">
      <van-radio name=0 @click="onFastDateChoose(fastChoose)">当月</van-radio>
      <van-radio name=1 @click="onFastDateChoose(fastChoose)">上月</van-radio>
      <van-radio name=2 @click="onFastDateChoose(fastChoose)">全年</van-radio>
      <van-radio name=3 @click="onFastDateChoose(fastChoose)">上年</van-radio>
    </van-radio-group>
    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 当期收支情况
    </van-divider>
    <div style=" height:80px;background: #FFF;margin-left: 20px">
      <div style="margin-top: 10px; float: left">
        <div v-show="this.totalIn!='0'">当期总收入： <span style="color: #42b983">￥{{
            this.totalIn
          }}</span></div>
        <div v-show="this.totalOut!='0'">当期总支出： <span style="color: #f54949">￥{{
            this.totalOut
          }}</span></div>
        <div>当期结余： ￥{{ this.totalEarn }}</div>
        <div v-show="this.handle==='2'">内部转账笔数： {{ this.flows.length }}</div>
      </div>
      <van-button type="default" round size="small" style=" float: right;margin-right: 20px" icon="gold-coin-o"
                  @click="()=>{this.typeMoneyListShow = true}">
        查看分类明细
      </van-button>
    </div>

    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 当期账单概览
    </van-divider>
    <van-cell-group :border="false">
      <div @click="toUpdateFlow(flow.id)" v-for="flow in flows" :key="flow.id">
        <van-swipe-cell>
          <template #left>
            <van-button size="small" square color="#8c8c8c" type="primary" class="delete-button"
                        @click="doShowNote(flow)">
              {{ doGetNotString(flow) }}
            </van-button>

          </template>
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
                <label v-if="useNote&&flow.note.length>0"
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
    <van-empty v-show="flows.length==0" description="当期无账单"/>

    <van-popup
        v-model="accountPopupShow"
        round
        position="bottom"
        :style="{ height: '50%' }"
    >
      <van-radio-group v-model="accountId">
        <van-cell-group inset v-for="account in this.allAccounts" :key="account.id">
          <van-cell :title=account.name clickable @click="onAccountChecked(account.id,account.name)">
            <template #right-icon>
              <van-radio :name=account.id></van-radio>
            </template>
          </van-cell>
        </van-cell-group>
      </van-radio-group>

    </van-popup>

    <van-popup
        v-model="morePopupShow"
        position="top"
        :style="{ width: '100%',height: '100%' ,background:'#F7F8FA' }"
    >
      <van-nav-bar fixed placeholder title="详细筛选条件" left-arrow right-text="筛选"
                   @click-right="onDetailScreenChoose">
        <template #left>
          <van-icon name="cross" size="18" @click="()=>{morePopupShow = false}"/>
        </template>
      </van-nav-bar>
      <van-divider :style="{ color: '#1989fa',}" content-position="left">账户选择</van-divider>

      <!--   账户选择   -->
      <van-cell-group :border="false" inset>
        <van-cell title="当前账户">
          <van-button type="default" round size="small" style=" float: right;margin-right: 20px"
                      icon="balance-o"
                      @click="()=>{accountPopupShow=true}">
            {{ this.accountName }}
          </van-button>
        </van-cell>
      </van-cell-group>
      <van-divider :style="{ color: '#1989fa',}" content-position="left">时间选择</van-divider>
      <!--   时间选择   -->
      <van-cell-group inset :border="false">

        <van-cell title="开始时间">
          <van-button type="default" round size="small" style=" float: right;"
                      icon="clock-o"
                      @click="()=>{showTimeDatePicker = true;setStartDate = true}">
            {{ startDate }}
          </van-button>
        </van-cell>
        <van-cell title="结束时间">
          <van-button type="default" round size="small" style=" float: right;"
                      icon="clock-o"
                      @click="()=>{showTimeDatePicker = true;setStartDate = false}">
            {{ endDate }}
          </van-button>
        </van-cell>
        <van-cell title="是否整月">
          <template #right-icon>
            <van-switch v-model="singleMonth" @click="fastChoose=-1" size="24px"/>
          </template>
        </van-cell>
        <van-cell title="筛选收藏">
          <template #right-icon>
            <van-switch v-model="collect" size="24px"/>
          </template>
        </van-cell>

      </van-cell-group>

      <van-divider :style="{ color: '#1989fa',}" content-position="left">资金流向</van-divider>
      <van-cell-group inset :border="false">

        <van-radio-group v-model="handle">
          <van-cell-group :border="false" style="background: #9e9e9e">
            <van-cell title="全部">
              <template #right-icon>
                <van-radio name='3'/>
              </template>
            </van-cell>
            <van-cell title="只看流入">
              <template #right-icon>
                <van-radio name='0'/>
              </template>
            </van-cell>
            <van-cell title="只看流出">
              <template #right-icon>
                <van-radio name='1'/>
              </template>
            </van-cell>
            <van-cell title="只看内部转账">
              <template #right-icon>
                <van-radio name='2'/>
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>

      </van-cell-group>
      <van-divider :style="{ color: '#1989fa',}" content-position="left">操作选择</van-divider>

      <van-cell-group inset :border="false">

        <van-checkbox-group v-model="chooseActions"
                            direction="horizontal">
          <van-cell name="handleRg" v-for="action in allActions" :key="action.id" :title=action.hname>
            <template #right-icon>
              <van-checkbox :name="action.id" shape="square"/>
            </template>
          </van-cell>
        </van-checkbox-group>

      </van-cell-group>

      <van-divider :style="{ color: '#1989fa',}" content-position="left">资金分类</van-divider>

      <van-tree-select
          :style="{margin:'15px'}"
          :items="allTypes"
          :active-id.sync="chooseTypes"
          :main-active-index.sync="activeIndex"
          @click-item="onTypesClick"
      />
      <div style="margin-left: 15px;margin-right: 15px;margin-bottom:20px;border-radius: 8px">
        <van-button type="info" style="margin-top: 5px" size="large" @click="()=>{excelDialogShow=true}">生成EXCEL
        </van-button>

      </div>
    </van-popup>

    <van-popup v-model="showTimeDatePicker" close-on-click-overlay  round position="bottom" :style="{height:'60%'}" @click-overlay="showTimeDatePicker = false">
      <van-datetime-picker
          v-if="setStartDate"
          show-toolbar
          title="选择开始日期"
          type="date"
          v-model="currentTime"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @cancel="showTimeDatePicker = false"
          @confirm="onDatePickerClick"
      />
      <van-datetime-picker
          v-else
          show-toolbar
          title="选择结束"
          type="date"
          v-model="currentTime"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @cancel="showTimeDatePicker = false"
          @confirm="onDatePickerClick"
      />
    </van-popup>

    <!--    <van-popup-->
    <!--        v-model="typeMoneyListShow"-->
    <!--        round-->
    <!--        position="bottom"-->
    <!--        :style="{ height: '70%' }"-->
    <!--    >-->

    <van-action-sheet v-model="typeMoneyListShow" title="当期分类收支明细">
      <van-cell-group>
        <div v-for="type in allTypesMoney" :key="type.typeId">
          <van-cell :value="'合计 ￥'+type.money">
            <template #title>
              <span class="custom-title">{{ type.typeName + " " }}</span>
              <van-tag type="primary">一级</van-tag>
            </template>
          </van-cell>
          <div style="margin-left: 30px">
            <van-cell v-for="typeChild in type.children" :key="typeChild.typeId" :title="typeChild.typeName"
                      :value="'￥'+typeChild.money"/>
          </div>
          <van-divider
              :style="{ color: '#1989fa', borderColor: '#1989fa',marginTop:'0px',marginBottom:'3px', padding: '0 16px' }"/>
        </div>

      </van-cell-group>
    </van-action-sheet>
    <van-dialog v-model="excelDialogShow" closeOnClickOverlay @confirm="onMakeExcelClick"
                @cancel="excelDialogShow=false" title="生成Excel" show-cancel-button>
      <van-field v-model="excelName" label="Excel标题" placeholder="请输入Excel标题"/>
    </van-dialog>
  </div>
</template>

<script>
import request from "../../utils/request";
import {Dialog, Toast} from "vant";

export default {
  name: "Screen",

  data() {
    return {
      totalIn: "",//总共收入
      totalOut: "",//总共支出
      totalEarn: "",//
      handle: 3,//操作 0流入，1流出，2内部转账，3全部
      accountId: this.$route.query.acid != null ? this.$route.query.acid : -1,//选择的账号
      accountName: "全部账号",
      startDate: "",//开始日期
      endDate: " ",//截止日期
      collect: false,//是否收藏
      singleMonth: true,//是否查看当月
      condition: "",//当前选择的筛选条件
      chooseTypes: [],//当前选择的分类
      chooseActions: [],//当前选择的操作
      useNote: false,//是否使用备注
      note: "",//备注

      //以下是网络内容
      allTypes: [],
      allTypesMoney: [],
      allActions: [],
      allAccounts: [],
      flows: [],

      //以下是日历
      minDate: new Date(2021, 10, 1),
      maxDate: new Date(),

      excelDialogShow: false,
      typeMoneyListShow: false,
      accountPopupShow: false,
      morePopupShow: false,
      showTimeDatePicker: false,
      setStartDate: true,
      currentTime: new Date(),
      fastChoose: '0',

      excelName: "",
      items: [],
      activeIndex: 0,

      /*以下是2.1版本新增*/
      chooseAccountActive: ['0'],
      chooseTimeActive: ['0'],
      chooseHandleActive: ['0'],
      chooseActionActive: ['0'],
      chooseTypeActive: ['0'],
    }
  },

  mounted() {
    this.startDate = this.fomatTime(new Date())
    this.endDate = ""
    this.showTimeDatePicker = false
    this.handle = 3
    this.doGetTypes()
    this.doGetActions()
    this.doGetAccounts()
    this.doGetCurrentFlow()
  },

  methods: {
    toUpdateFlow(flowid) {
      this.$router.push({path: "/flow/add", query: {flowId: flowid}});
    },
    onMakeExcelClick() {
      if (this.excelName == null || this.excelName == "") {
        Toast.fail('请输入Excel标题');
        return
      }
      request({
        url: "/screen/makeExcel?excelName=" + this.excelName,
        method: "post",
        data: {
          chooseHandle: this.handle,
          accountId: this.accountId,
          startDate: this.startDate,
          endDate: this.endDate,
          singleMonth: this.singleMonth,
          collect: this.collect,
          types: this.chooseTypes,
          actions: this.chooseActions
        }
      }).then(() => {
        this.excelName = ""
        this.excelDialogShow = false
      }).catch(() => {
        this.excelName = ""
        this.excelDialogShow = false
      });
    },

    formatter(type, val) {
      if (type === 'year') {
        return `${val}年`;
      }
      if (type === 'month') {
        return `${val}月`;
      }
      if (type === 'day') {
        return `${val}日`;
      }
      return val;
    },
    onClickLeft() {
      this.useNote = !this.useNote
      if (!this.useNote) {
        this.note = ""
        this.doGetCurrentFlow()
      }
    },

    onNoteSearch() {
      this.doGetCurrentFlow()
    },

    doGetCurrentFlow() {
      request({
        url: "/screen/getFlowByScreen",
        method: "post",
        data: {
          chooseHandle: this.handle,
          accountId: this.accountId,
          startDate: this.startDate,
          endDate: this.endDate,
          singleMonth: this.singleMonth,
          collect: this.collect,
          types: this.chooseTypes,
          actions: this.chooseActions,
          note: this.note
        }
      }).then((response) => {
        console.log(response.data.data);
        const flow = response.data.data;
        this.flows = response.data.data.flows;
        this.totalIn = flow.totalIn;
        this.totalOut = flow.totalOut;
        this.totalEarn = flow.totalEarn;
        this.allTypesMoney = flow.typeList;
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
      })
      this.doSetCondition()
    },

    doSetCondition() {
      this.condition = "当期日期：" + this.startDate + "\n是否整月:" + this.singleMonth
    },

    doGetActions() {
      request({
        url: "/action/getAction",
        method: "get"
      }).then((response) => {
        this.allActions = response.data.data;

        console.log(this.allActions);
      });
    },

    doGetAccounts() {
      request({
        url: "/account/getAccountNoLimit",
        method: "get",
      })
          .then((response) => {
            const baseData = response.data.data;
            baseData.unshift({
              id: -1, name: "全部账户"
            })
            baseData.forEach((item) => {
              item.money = "￥" + item.money;
              item.exemptMoney = "￥" + item.exemptMoney;
              if (this.accountId == item.id) {
                this.accountName = item.name
              }
            });
            this.allAccounts = baseData;
            console.log(this.allAccounts);
          })
          .catch((error) => {
            console.log(error);
          });
    },

    doGetTypes() {
      request({
        url: "/type/getType/noLimit",
        method: "get",
      })
          .then((response) => {
            const allTypes = response.data.data;
            allTypes.forEach((item) => {
              item.text = item.tname
              if (item.childrenTypes != null) {
                const chileTypes = item.childrenTypes;
                chileTypes.unshift({
                  tname: "选择当前大类",
                  id: item.id,
                  parent: item.parent
                })
                chileTypes.forEach((children) => {
                  children.text = children.tname
                })
              } else {
                var child = {
                  tname: "选择当前大类",
                  id: item.id,
                  text: "选择当前大类",
                  parent: item.parent
                }
                item.childrenTypes = [child]
              }

              item.children = item.childrenTypes
            })
            this.allTypes = allTypes
            console.log(this.allTypes)
          })
    },

    onTypesClick(data) {
      console.log(data)

    },

    fomatTime(date) {
      var year = date.getFullYear(),
          month = date.getMonth() + 1,//月份是从0开始的
          day = date.getDate()

      return year + '-' +
          (month < 10 ? '0' + month : month) + '-' +
          (day < 10 ? '0' + day : day) + ''
    },

    onDetailScreenChoose() {
      this.morePopupShow = false
      this.doGetCurrentFlow()
    },


    onAccountChecked(check, accountName) {
      console.log(check)
      this.accountId = check
      this.accountName = accountName
      this.accountPopupShow = false
    },

    onFastDateChoose(check) {
      this.singleMonth = true
      var data = new Date()
      switch (check) {
        case  '0':
          this.startDate = this.fomatTime(new Date(data.getFullYear(), data.getMonth(), 1))
          this.endDate = ""
          this.singleMonth = true
          break
        case  '1':
          this.startDate = this.fomatTime(new Date(data.getFullYear(), data.getMonth() - 1, 1))
          this.endDate = ""
          this.singleMonth = true
          break
        case  '2':
          this.startDate = this.fomatTime(new Date(data.getFullYear(), 0, 1))
          this.endDate = this.fomatTime(new Date(data.getFullYear(), data.getMonth(), data.getDate()))
          this.singleMonth = false
          break
        case  '3':
          this.startDate = this.fomatTime(new Date(data.getFullYear() - 1, 0, 1))
          this.endDate = this.fomatTime(new Date(data.getFullYear() - 1, 11, 31))
          this.singleMonth = false
          break
      }
      console.log(this.startDate)
      console.log(this.endDate)
      console.log(this.singleMonth)
      this.doGetCurrentFlow()
    },

    onDatePickerClick(value) {
      this.fastChoose = -1
      this.showTimeDatePicker = false
      if (this.setStartDate) {
        this.startDate = this.fomatTime(value)
      } else {
        this.endDate = this.fomatTime(value)
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

    doShowNote(flow) {
      if (flow.note != null && flow.note.length > 4) {
        Dialog.alert({
          title: '备注',
          message: flow.note,
        }).then(() => {
          // on close
        });
      }
    },
  }
}
</script>

<style scoped>
.delete-button {
  height: 100%;
  white-space: pre-wrap;
}
</style>