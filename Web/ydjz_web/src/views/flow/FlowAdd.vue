<template >
  <div style="height:100%;background: #eeeeee">
    <van-nav-bar v-if="this.$route.query.flowId==null" title="新增账单" left-arrow @click-left="onClickLeft"/>
    <van-nav-bar v-else title="修改账单" left-arrow @click-left="onClickLeft"/>
    <van-cell-group>
      <van-field
          input-align="right"
          v-model="money"
          type="number"
          label="账单金额"
          placeholder="请输入账单金额"
      />
      <van-cell title="选择收支" is-link @click="onActionClick">
        <template #default>
          <van-tag :type="chooseAction.style">{{ chooseAction.hName }}</van-tag>
          <van-tag
              v-show="chooseAction.exempt"
              style="margin-left: 10px"
              color="gray"
              plain
              type="action.style"
          >{{ chooseAction.value }}
          </van-tag>
        </template>
      </van-cell>
      <van-cell :title=" chooseAction.handle==2?'选择源账户':'选择账户'" is-link @click="onAccountClick(1)"
                :value="chooseAccount.name"/>

      <van-cell v-show="chooseAction.handle==2" title="选择目标账户" is-link @click="onAccountClick(2)"
                :value="chooseToAccount.name"/>

      <van-cell title="账单分类" :value="chooseType.tName" is-link @click="onTypeClick"/>

      <van-cell title="账单日期" :value="chooseDate" is-link @click="onCalanderClick"/>

      <van-field name="switch" label="是否收藏">
        <template #right-icon>
          <van-switch v-model="isCollect" size="20"/>
        </template>
      </van-field>

      <van-field
          v-model="note"
          rows="2"
          autosize
          label="备注"
          type="textarea"
          maxlength="50"
          placeholder="请输入备注"
          show-word-limit
          input-align="right"
      />
    </van-cell-group>
    <van-action-sheet v-if="popupStyle<=2" v-model="actionShow" :title="popupTitle">
      <van-cell-group v-if="popupStyle == 0">
        <van-cell
            v-for="action in allActions"
            :key="action.id"
            @click="onChooseAction(action)">
          <template #title>
            <span class="custom-title">{{ action.hName }}</span>
          </template>
          <template #label>
            <van-tag :type="action.style">{{ action.handleText }}</van-tag>
            <van-tag
                v-show="action.exempt"
                style="margin-left: 10px"
                color="gray"
                plain
                type="action.style"
            >{{ action.value }}
            </van-tag
            >
          </template>
        </van-cell>
      </van-cell-group>

      <van-cell-group v-if="popupStyle==1||popupStyle==2">
        <van-cell v-for="account in allAccounts" :key="account.id" :title="account.name" :value="account.money"
                  :label="account.note" @click="onChooseAccount(account,popupStyle)"/>
      </van-cell-group>
    </van-action-sheet>
    <van-popup v-model="cascaderShow" round position="bottom">
      <van-cascader
          v-model="cascaderValue"
          title="选择账单分类"
          :options="allTypes"
          active-color="#1989fa"
          @close="cascaderShow = false"
          :field-names="cascaderNames"
          @finish="onChooseCascader"
      />
    </van-popup>
    <van-calendar v-model="calanderShow" :show-confirm="false" color="#1989fa" :min-date="minDate"
                  :max-date="maxDate " @confirm="onChooseCalander"/>

    <van-cell-group v-for="child in childMoneyItem" :key="child.index" inset style="margin-top: 10px;margin-bottom: 10px">
      <van-swipe-cell>
        <van-field
            input-align="left"
            v-model="child.money"
            type="number"
            label="账单金额"
            placeholder="请输入追加账单金额"
        />
        <van-field v-model="child.note" label="追加备注" placeholder="请输入追加备注"/>
        <template #right>
          <van-button square type="danger" text="删除" style="height: 100%" @click="doRemoveMoneyItem(child)"/>
        </template>
      </van-swipe-cell>
    </van-cell-group>

    <div style="margin: 16px">
      <van-button @click="doAddNewItemMoney" style="margin-bottom: 5px" round block type="warning" native-type="submit">
        追加分账单
      </van-button>

      <van-button @click="onSubmit" round block type="info" native-type="submit"
      >{{ this.$route.query.flowId != null ? "修改" : "提交" }}
      </van-button>
    </div>
  </div>
</template>

<script>
import request from "../../utils/request";
import {Dialog, Toast} from "vant";

export default {
  name: "FlowAdd",
  data() {
    return {
      childMoneyItem: [],
      money: "",
      actionShow: false,
      calanderShow: false,
      cascaderShow: false,
      popupStyle: 0,
      popupTitle: "",

      chooseAction: {}, //已选择的action
      allActions: [], //全部的action

      chooseAccount: {},
      chooseToAccount: {},
      allAccounts: [],

      cascaderValue: '',//已选则分类的id
      chooseType: {tName: "", id: 0},
      allTypes: [],

      chooseDate: "",

      isCollect: false,

      note: "",
      submitMoney:"",
      submitNote:"",
      //以下是分类级联
      cascaderNames: {
        text: 'tName',
        value: 'id',
        children: 'childrenTypes',
      },

      minDate: new Date(2021, 0, 1),
      maxDate: new Date(),
    };
  },
  mounted() {
    if (this.$route.query.flowId != null) {
      this.doGetCurrentFlow()
    }
    this.doGetTypes()
    this.doGetActions()
    this.doGetAccounts()
  },
  methods: {
    doRemoveMoneyItem(item){
      console.log(item)
      this.childMoneyItem.splice(this.childMoneyItem.indexOf(item),1)
    },
    doAddNewItemMoney() {
      var childItem = {
        index: Date.now(),
        note: ""
      }
      this.childMoneyItem.push(childItem)
      console.log( this.childMoneyItem)
    },

    doGetCurrentFlow() {
      request({
        url: "/flow/getFlow/" + this.$route.query.flowId,
        method: "get"
      }).then(response => {
        const flow = response.data.data;
        console.log(flow)
        this.money = flow.money
        this.chooseAccount = flow.account
        this.chooseAccount.name = flow.account.aName
        this.chooseAction = this.setActionStyle(flow.action)
        this.chooseType = flow.type
        this.isCollect = flow.collect
        this.note = flow.note
        if (flow.action.handle == "2") {
          this.chooseToAccount = flow.accountTo
          this.chooseToAccount.name = flow.accountTo.aName
        }
        this.chooseDate = flow.fDate
      })
    },

    setActionStyle(action) {
      action.value = action.exempt ? "不计入总金额" : "";
      action.handleText =
          action.handle === 0
              ? "账户金额增加"
              : action.handle === 1
                  ? "账户金额减少"
                  : "账户金额不变";
      action.style =
          action.handle === 0
              ? "success"
              : action.handle === 1
                  ? "danger"
                  : "primary";
      return action
    },
    onSubmit() {
      if (!this.doVertify()) {
        return
      }
      var moneyInt = parseFloat(this.money)
      this.submitNote = this.note

      if (this.childMoneyItem.length>0&&!this.submitNote.includes("(￥")){
        this.submitNote = this.submitNote+"(￥"+this.money+")"
      }
      this.childMoneyItem.forEach(chileMoney=>{
        if (chileMoney.money!=null){
          moneyInt = moneyInt+parseFloat(chileMoney.money)
          this.submitNote = this.submitNote+"\n"+chileMoney.note+"(￥"+chileMoney.money+")"
        }
      })
      if (this.childMoneyItem.length>0){
        this.submitMoney = moneyInt+""
      } else {
        this.submitMoney = this.money
      }
      Dialog.confirm({
        title: '请确认账单',
        message:
            '总金额: ￥' + this.submitMoney +'\n'+
        "备注："+this.submitNote,
        confirmButtonText:"确认无误"
      })
          .then(() => {
          this.doSubmitRequest()
          })
          .catch(() => {
            // on cancel
          });
    },

    doSubmitRequest(){
      const api = this.$route.query.flowId == null ? "/flow/addFlow" : "/flow/updateFlow/" + this.$route.query.flowId
      const method = this.$route.query.flowId == null ? "post" : "put"
      request({
        url: api,
        method: method,
        data: {
          money: this.submitMoney,
          fDate: this.chooseDate,
          actionId: parseInt(this.chooseAction.id),
          accountId: parseInt(this.chooseAccount.id),
          accountToId: parseInt(this.chooseToAccount.id),
          typeId: parseInt(this.chooseType.id),
          collect: this.isCollect,
          note: this.submitNote
        }
      }).then(() => {
        this.$router.go(-1)
      })
    },

    doVertify() {
      if (this.money == "" || this.money == null) {
        Toast.fail("请输入金额")
        return false;
      }
      if (this.chooseAction.id == null) {
        Toast.fail("请选择收支")
        return false;
      }
      if (this.chooseAccount.id == null) {
        Toast.fail("请选择账户")
        return false;
      }
      if (this.chooseAction.handle == 2) {
        if (this.chooseToAccount.id == null) {
          Toast.fail("请选择目标账户")
          return false;
        }
      }
      if (this.chooseType.id == "" || this.chooseType.id == null) {
        Toast.fail("请选择分类")
        return false;
      }
      if (this.chooseDate == "") {
        Toast.fail("请选择账单日期")
        return false
      }
      return true
    },

    onClickLeft() {
      this.$router.go(-1);
    },

    onCalanderClick() {
      this.calanderShow = true;
    },

    onTypeClick() {
      this.cascaderShow = true;
    },

    onAccountClick(popupStyle) {
      this.actionShow = true;
      this.popupTitle = "选择账户";
      this.popupStyle = popupStyle;
    },

    onActionClick() {
      this.actionShow = true;
      this.popupTitle = "选择账单分类";
      this.popupStyle = 0;
    },

    doGetActions() {
      request({
        url: "/action/getAction",
        method: "get"
      }).then((response) => {
        this.allActions = response.data.data;
        this.allActions.forEach((action) => {
          this.setActionStyle(action)
        });
        console.log(this.allActions);
      });
    },

    doGetAccounts() {
      request({
        url: "/account/getAccount",
        method: "get",
      })
          .then((response) => {
            const baseData = response.data.data;
            baseData.forEach((item) => {
              item.money = "￥" + item.money;
              item.exemptMoney = "￥" + item.exemptMoney;
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
        url: "/type/getType",
        method: "get",
      })
          .then((response) => {
            this.allTypes = response.data.data;
            console.log(this.allTypes)
          })
    },

    onChooseAction(action) {
      this.actionShow = false;
      this.chooseAction = action;
      this.chooseToAccount = {};
    },

    onChooseAccount(account, popupStyle) {
      this.actionShow = false;
      if (popupStyle == 1) {
        this.chooseAccount = account
      } else {
        this.chooseToAccount = account
      }
    },

    onChooseCascader({selectedOptions}) {
      this.cascaderShow = false;
      this.chooseType.id = this.cascaderValue
      this.chooseType.tName = selectedOptions.map((option) => option.tName).join('——');
      console.log(this.chooseType)
    },

    formatDate(date) {
      return `${date.getFullYear()}-${((date.getMonth() + 1) + "").padStart(2, '0')}-${(date.getDate() + "").padStart(2, '0')}`;
    },

    onChooseCalander(date) {
      this.calanderShow = false;
      this.chooseDate = this.formatDate(date);
    },


  }
};
</script>

<style scoped></style>
