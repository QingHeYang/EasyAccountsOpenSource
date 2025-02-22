<template>
  <div style="width:100vw; height:100vh; background: #F7F8FA">
    <van-nav-bar v-if="this.$route.query.flowId==null" title="新增明细" left-arrow @click-left="onClickLeft"
                 right-text="快记模板" @click-right="fastPopupShow = true"/>
    <van-nav-bar v-else title="修改明细" left-arrow @click-left="onClickLeft"/>
    <van-cell-group>
      <!-- 新增明细编号显示  v2.5版本 -->
      <van-cell 
        v-if="$route.query.flowId" 
        title="明细编号" 
        :value="'#' + $route.query.flowId"
        :value-style="{ color: '#999' }"
      />
      
      <van-field
          input-align="right"
          v-model="money"
          type="number"
          label="明细金额"
          placeholder="请输入明细金额"
      />
<!--      @touchstart.native.stop="keyboardShow = true"-->
      <van-cell title="选择收支" is-link @click="onActionClick">
        <template #default>
          <van-tag :type="chooseAction.style">{{ chooseAction.hname }}</van-tag>
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

      <van-cell title="明细分类" :value="chooseType.tname" is-link @click="onTypeClick"/>

      <van-cell title="明细日期" :value="chooseDate" is-link @click="onCalanderClick"/>

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
    <van-action-sheet v-if="popupStyle<=2" v-model:show="actionShow" :title="popupTitle">
      <van-cell-group v-if="popupStyle == 0">
        <van-cell
            v-for="action in allActions"
            :key="action.id"
            @click="onChooseAction(action)">
          <template #title>
            <span class="custom-title">{{ action.hname }}</span>
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
    <van-popup v-model:show="typeCascaderShow" round position="bottom">
      <van-cascader
          v-model="cascaderValue"
          title="选择明细分类"
          :options="allTypes"
          active-color="#1989fa"
          @close="typeCascaderShow = false"
          :field-names="cascaderNames"
          @finish="onChooseCascader"
      />
    </van-popup>
    <van-calendar v-model:show="calanderShow" :show-confirm="false" color="#1989fa" :min-date="minDate"
                  :max-date="maxDate " @confirm="onChooseCalendar"/>

    <!--  追加明细 1.6版本  -->
    <van-cell-group v-for="child in childMoneyItem" :key="child.index" inset
                    style="margin-top: 10px;margin-bottom: 10px">
      <van-swipe-cell>
        <van-field
            input-align="left"
            v-model="child.money"
            type="number"
            label="明细金额"
            placeholder="请输入追加明细金额"
        />
        <van-field v-model="child.note" label="追加备注" placeholder="请输入追加备注"/>
        <template #right>
          <van-button square type="danger" text="删除" style="height: 100%" @click="doRemoveMoneyItem(child)"/>
        </template>
      </van-swipe-cell>
    </van-cell-group>
    <!--  追加明细 1.6版本  -->
    <div style="margin: 16px">
      <van-button @click="doAddNewItemMoney" style="margin-bottom: 5px" round block type="warning" native-type="submit">
        追加分明细
      </van-button>

      <van-button @click="onSubmitBtnClick" round block type="primary"
      >{{ this.$route.query.flowId != null ? "修改" : "提交" }}
      </van-button>
    </div>

    <!--  快记模板 2.1版本  -->
    <van-popup
        v-model:show="fastPopupShow"
        position="top"
        :style="{ width: '100%',height: '100%' ,background:'#F7F8FA' }"
    >
      <van-nav-bar title="选择模板" left-arrow fixed placeholder right-text="模板管理" @click-right="fastNavToTemplateManage">
        <template #left>
          <van-icon name="cross" size="18" @click="fastPopupShow=false"/>
        </template>
      </van-nav-bar>
      <van-cell-group inset :border="false" style="margin-top: 10px;margin-bottom: 10px">
        <van-collapse :border="false" v-model="activeNames">
          <van-collapse-item title="标签筛选" :toggle="tagChooseShow" name="1">
            <template #value>
              <van-tag v-if="chooseTag.id!=null" :color="chooseTag.color" closeable
                       @close="chooseTag = {};getAllTemplate()">{{ chooseTag.name }}
              </van-tag>
            </template>
            <div v-if="allTags.length !== 0" class="tags-container">
              <div class="tag-item" v-for="tag in allTags" :key="tag.id"
                   @click="chooseTag = tag;getAllTemplate();tagChooseShow = false">
                <van-tag size="small" :color="tag.color">{{ tag.name }}</van-tag>
              </div>
            </div>
            <van-empty v-else description="暂无标签" style="margin-top: 10px"/>

          </van-collapse-item>

        </van-collapse>
      </van-cell-group>

      <van-cell-group :border="false" inset style="margin-top: 10px;">
        <van-cell title="模板列表" :border="false"/>
        <van-grid :border="true" :column-num="2" :gutter="10" style="margin-bottom: 10px" :center="false"
                  v-if="allTemplates.length!=0">
          <van-grid-item v-for="template in allTemplates" :key="template.id">
            <template #default>
              <div class="template-container" @click="fastChooseClick(template)">
                <div class="template-info">
                  <div class="template-name">{{ template.name }}</div>
                  <van-tag v-if="template.tag" :color="template.tag.color">{{ template.tag.name }}</van-tag>
                </div>
                <div class="template-action">
                  <van-button plain hairline size="small" type="primary" style="margin-left: 10px"
                              @click.stop="fastDialogClick(template)">详情
                  </van-button>
                </div>
              </div>
            </template>
          </van-grid-item>
        </van-grid>
        <van-empty v-else description="暂无模板" style="margin-top: 10px"/>
      </van-cell-group>
    </van-popup>

    <van-dialog v-model:show="fastDialogShow" closeOnClickOverlay cancel-button-text="编辑" confirm-button-text="选择"
                cancel-button-color="#3D8AF2" @cancel="fastDialogToEdit(chooseTemplate.id)" :title="chooseTemplate.name"
                @confirm="fastChooseClick(chooseTemplate)"
                show-cancel-button>
      <van-cell-group :border="false" v-model="chooseTemplate.show">

        <van-cell v-if="chooseTemplate.money" title="金额" :value="chooseTemplate.money"/>
        <van-cell v-if="chooseTemplate.actionId" title="收支">
          <template #default>
            <van-tag plain :type="chooseTemplate.action.style">{{ chooseTemplate.action.hname }}</van-tag>
          </template>
        </van-cell>
        <van-cell v-if="chooseTemplate.accountId" title="账户" :value="chooseTemplate.account.name"/>
        <van-cell v-if="chooseTemplate.accountToId" title="目标账户" :value="chooseTemplate.accountTo.name"/>
        <van-cell v-if="chooseTemplate.typeId" title="分类选择" :value="chooseTemplate.type.tname"/>
        <van-cell v-if="chooseTemplate.dateTypeStr" title="日期类型"
                  :value="chooseTemplate.dateTypeStr==='1'?'补上月':'记本月'"/>
        <van-cell title="标签" name="1">
          <template #default>
            <div style="display: flex; justify-content: flex-end;">
              <div v-if="chooseTemplate.tag">
                <van-tag :color="chooseTemplate.tag.color" style="margin-right: 15px">{{ chooseTemplate.tag.name }}
                </van-tag>
              </div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </van-dialog>
  </div>
</template>

<script>
import {showConfirmDialog, showFailToast, showSuccessToast} from "vant";
import template from "@/views/setting/template/Template.vue";

export default {
  name: "FlowAdd",
  computed: {
    template() {
      return template
    },
  },
  data() {
    return {
      // 2.1版本
      tagChooseShow: false,
      activeNames: [],
      allTemplates: [],
      chooseTemplate: {},
      allTags: [],
      chooseTag: {},
      fastPopupShow: false,
      fastDialogShow: false,

      keyboardShow: false,
      keyboardValue: "",
      childMoneyItem: [],
      money: "",
      calanderShow: false,
      typeCascaderShow: false,
      actionShow: false,
      popupStyle: 0,
      popupTitle: "",

      chooseAction: {}, //已选择的action
      allActions: [], //全部的action

      chooseAccount: {},
      chooseToAccount: {},
      allAccounts: [],

      cascaderValue: '',//已选则分类的id
      chooseType: {},
      allTypes: [],

      chooseDate: "",

      isCollect: false,

      note: "",
      submitMoney: "",
      submitNote: "",
      //以下是分类级联
      cascaderNames: {
        text: 'tname',
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

    } else {
      this.getAllTags()
    }
    this.doGetActions()
    this.doGetAccounts()
  },
  methods: {
    fastChooseClick(template) {
      this.fastPopupShow = false;
      this.fastDialogShow = false;
      showSuccessToast(template.name);
      this.money = template.money;
      this.chooseAccount = template.account;
      if (template.action != null) {
        this.chooseAction = this.setActionStyle(template.action);
        if (this.chooseAction.id != null) {
          this.doGetTypes()
        }

        if (template.action.handle.toString() == "2") {
          this.chooseToAccount = template.accountTo
          this.chooseToAccount.name = template.accountTo.name
        }
      }

      this.chooseType = template.type;
      if (template.dateType != null) {
        if (template.dateType.toString() === "0") {
          this.chooseDate = this.formatDate(new Date())
        } else {
          //选择的是上月最后一天
          var date = new Date();
          date.setDate(0);
          this.chooseDate = this.formatDate(date)
        }
      }

    },
    fastDialogClick(template) {
      this.chooseTemplate = template;
      this.fastDialogShow = true;
      // 阻止冒泡可以放在这里或直接在模板中使用 .stop 修饰符
    },
    fastDialogToEdit(id) {
      this.fastDialogShow = false;
      this.$router.push({path: "/template/add", query: {templateId: id}});
    },
    fastNavToTemplateManage() {
      this.$router.push({path: "/setting/template"});
    },

    getAllTags() {
      this.$http({
        url: "/tag/getTags",
        method: "get",
      }).then((response) => {
        this.allTags = response.data.data;
        this.getAllTemplate()
        console.log(this.allTags);
      }).catch((error) => {
        console.log(error);
      });
    },

    getAllTemplate() {
      this.$http({
        url: this.chooseTag.id != null ? "/template/getAllTemplatesByTag/" + this.chooseTag.id : "/template/getAllTemplates",
        method: "get",
      }).then((response) => {
        this.allTemplates = response.data.data;
        this.allTemplates.forEach((template) => {
          if (template.action) {
            template.action = this.setActionStyle(template.action);
          }
          if (template.date != null) {
            template.dateTypeStr = template.dateType.toString();
          } else {
            template.dateTypeStr = "";
          }
        });
        console.log(this.allTemplates);
      }).catch((error) => {
        console.log(error);
      });
    },

    doRemoveMoneyItem(item) {
      console.log(item)
      this.childMoneyItem.splice(this.childMoneyItem.indexOf(item), 1)
    },
    doAddNewItemMoney() {
      var childItem = {
        index: Date.now(),
        note: ""
      }
      this.childMoneyItem.push(childItem)
      console.log(this.childMoneyItem)
    },

    doGetCurrentFlow() {
      this.$http({
        url: "/flow/getFlow/" + this.$route.query.flowId,
        method: "get"
      }).then(response => {
        const flow = response.data.data;
        console.log(flow)
        this.money = flow.money
        this.chooseAccount = flow.account
        this.chooseAccount.name = flow.account.aname
        this.chooseAction = this.setActionStyle(flow.action)
        this.chooseType = flow.type
        console.log(this.chooseType)
        this.isCollect = flow.collect
        this.note = flow.note
        if (flow.action.handle == "2") {
          this.chooseToAccount = flow.accountTo
          this.chooseToAccount.name = flow.accountTo.aname
        }
        this.chooseDate = flow.fdate
        this.doGetTypes()
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

    onSubmitHandle() {
      var moneyInt = parseFloat(this.money)
      this.submitNote = this.note

      if (this.childMoneyItem.length > 0 && !this.submitNote.includes("(￥")) {
        this.submitNote = this.submitNote + "(￥" + this.money + ")"
      }
      this.childMoneyItem.forEach(chileMoney => {
        if (chileMoney.money != null) {
          moneyInt = moneyInt + parseFloat(chileMoney.money)
          this.submitNote = this.submitNote + "\n" + chileMoney.note + "(￥" + chileMoney.money + ")"
        }
      })
      if (this.childMoneyItem.length > 0) {
        this.submitMoney = moneyInt + ""
      } else {
        this.submitMoney = this.money
      }
      showConfirmDialog({
        title: '请确认明细',
        message:
            '总金额: ￥' + this.submitMoney + '\n' +
            "备注：" + this.submitNote,
        confirmButtonText: "确认无误"
      })
          .then(() => {
            this.doSubmitRequest()
          })
          .catch(() => {
            // on cancel
          });
    },

    onSubmitBtnClick() {
      if (!this.doVertify()) {
        return
      }
      if (this.chooseType.action != null && this.chooseType.action.id != this.chooseAction.id) {
        return showConfirmDialog({
          title: '提示',
          message:
              '当前分类存在修改收支类型的情况\n是否继续提交？',
          confirmButtonText: "继续提交"
        })
            .then(() => {
              this.onSubmitHandle()
            })
            .catch(() => {
            });
      } else {
        this.onSubmitHandle()
      }
    },

    doSubmitRequest() {
      const api = this.$route.query.flowId == null ? "/flow/addFlow" : "/flow/updateFlow/" + this.$route.query.flowId
      const method = this.$route.query.flowId == null ? "post" : "put"
      this.$http({
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
        showFailToast("请输入金额")
        return false;
      }
      if (this.chooseAction.id == null) {
        showFailToast("请选择收支")
        return false;
      }
      if (this.chooseAccount.id == null) {
        showFailToast("请选择账户")
        return false;
      }
      if (this.chooseAction.handle == 2) {
        if (this.chooseToAccount.id == null) {
          showFailToast("请选择目标账户")
          return false;
        }
      }
      if (this.chooseType.id == "" || this.chooseType.id == null) {
        showFailToast("请选择分类")
        return false;
      }
      if (this.chooseDate == "") {
        showFailToast("请选择明细日期")
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
      if (this.chooseAction.id == null) {
        showFailToast("请先选择收支")
        return;
      }
      this.typeCascaderShow = true;
    },

    onAccountClick(popupStyle) {
      this.actionShow = true;
      this.popupTitle = "选择账户";
      this.popupStyle = popupStyle;
    },

    onActionClick() {
      this.actionShow = true;
      this.popupTitle = "选择明细收支";
      this.popupStyle = 0;
    },

    doGetActions() {
      this.$http({
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
      this.$http({
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
      this.$http({
        url: "/type/getTypeByActionId/" + this.chooseAction.id,
        method: "get",
      })
          .then((response) => {
            this.allTypes = response.data.data;
            console.log(this.allTypes)
          })
    },

    onChooseAction(action) {
      this.actionShow = false;
      if (action === this.chooseAction) {
        return
      }
      this.chooseAction = action;
      this.chooseToAccount = {};
      this.chooseType = {}
      this.doGetTypes()
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
      this.typeCascaderShow = false;
      this.chooseType.id = this.cascaderValue
      this.chooseType.tname = selectedOptions.map((option) => option.tname).join('/');

      console.log(this.chooseType)
    },

    formatDate(date) {
      return `${date.getFullYear()}-${((date.getMonth() + 1) + "").padStart(2, '0')}-${(date.getDate() + "").padStart(2, '0')}`;
    },

    onChooseCalendar(date) {
      this.calanderShow = false;
      this.chooseDate = this.formatDate(date);
      console.log(this.chooseDate)
    },


  }
};
</script>

<style scoped>
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px; /* 设置标签之间的间隔 */
  padding: 15px; /* 容器的内边距 */
}

.tag-item {
  margin-bottom: 5px; /* 增加标签下方的间隔，避免视觉上的拥挤 */
}

.template-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px; /* 增加内部间距 */
}

.template-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start; /* 左对齐文本和标签 */
}

.template-name {
  font-size: 14px; /* 字体大小调整 */
  margin-bottom: 4px; /* 为名称和标签之间添加间距 */
}

.template-tag {
  display: block; /* 确保标签作为独立的行显示 */
}

.template-action {
  text-align: right; /* 右侧对齐详情按钮 */
}

</style>
