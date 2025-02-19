<template>
  <div style="width:100vw; height:100vh; background: #F7F8FA">
    <van-nav-bar v-if="this.$route.query.templateId==null" fixed placeholder
                 title="添加模板"
                 left-arrow
                 right-text="管理标签"
                 @click-left="leftClick"
                 @click-right="toTagManage"
    />
    <van-nav-bar v-else fixed placeholder
                 title="编辑模板"
                 right-text="管理标签"
                 left-arrow
                 @click-left="leftClick"
                 @click-right="toTagManage"
    />

    <van-cell-group :border="false" inset :style="{marginTop:'20px'}">
      <van-field
          input-align="right"
          v-model="template.name"
          label="模板名称"
          required
          placeholder="请输入模板名称"/>
      <van-field
          input-align="right"
          v-model="template.money"
          type="number"
          label="模板金额"
          placeholder="请输入模板金额"
      />
    </van-cell-group>
    <van-cell-group :border="false" inset :style="{marginTop:'20px'}">
      <van-cell title="选择模板收支" is-link @click="onActionClick">
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

      <van-cell :title=" chooseAction.handle==2?'选择模板源账户':'选择模板账户'" is-link @click="onAccountClick(1)"
                :value="chooseAccount.name"/>

      <van-cell v-show="chooseAction.handle==2" title="选择模板目标账户" is-link @click="onAccountClick(2)"
                :value="chooseAccountTo.name"/>

      <van-cell title="模板账单分类" :value="chooseType.tname" is-link @click="onTypeClick"/>

      <van-cell title="模板账单日期">
        <template #icon>

          <van-icon name="question-o" @click="onDateClick"
                    :style="{ marginRight:'5px',display: 'flex', justifyContent: 'center', alignItems: 'center' }"/>
        </template>
        <template #right-icon>
          <van-radio-group v-model="dateTypeStr" direction="horizontal">
            <van-radio name="1" checked-color="#ee0a24">补上月</van-radio>
            <van-radio name="0">记本月</van-radio>
          </van-radio-group>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group :border="false" inset :style="{marginTop:'20px'}">

      <van-collapse :border="false" v-model="activeNames" accordion>
        <van-collapse-item title="标签筛选" :toggle="chooseTag" name="1">
          <template #value>
            <van-tag v-if="chooseTag.id!=null" :color="chooseTag.color" closeable size="large"
                     @close="chooseTag = {};">{{ chooseTag.name }}
            </van-tag>
          </template>
          <div v-if="allTags.length !== 0" class="tags-container">
            <div class="tag-item" v-for="tag in allTags" :key="tag.id"
                 @click="chooseTag = tag;">
              <van-tag size="large" :color="tag.color">{{ tag.name }}</van-tag>
            </div>
          </div>
          <van-empty v-else description="暂无标签" style="margin-top: 10px"/>

        </van-collapse-item>
      </van-collapse>
    </van-cell-group>

    <div style="margin: 20px">
      <van-button type="success" size="large" @click="onSubmit">{{ isEdit ? "修改" : "新建" }}</van-button>
      <van-button v-if="isEdit" type="danger" size="large" style="margin-top: 5px" @click="deleteTemplate">删除
      </van-button>
    </div>

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
          title="选择账单分类"
          :options="allTypes"
          active-color="#1989fa"
          @close="typeCascaderShow = false"
          :field-names="cascaderNames"
          @finish="onChooseCascader"
      />
    </van-popup>
  </div>
</template>
<script>
import {showConfirmDialog, showDialog, showFailToast} from "vant";

export default {
  name: "TemplateAdd.vue",
  data() {
    return {

      activeNames: ['1'],
      tagManageShow: true,
      isEdit: this.$route.query.templateId != null,

      popupStyle: 0,
      popupTitle: "",

      //标签相关
      allTags: [],
      chooseTag: {},

      //收支相关
      actionShow: false,
      allActions: [],
      chooseAction: {},

      //账户相关
      allAccounts: [],
      chooseAccount: {},
      chooseAccountTo: {},

      //分类相关
      cascaderValue: '',//已选则分类的id
      chooseType: {},
      showTname: "",
      allTypes: [],
      typeCascaderShow: false,
      cascaderNames: {
        text: 'tname',
        value: 'id',
        children: 'childrenTypes',
      },

      dateTypeStr: "",
      template: {
        id: "",
        name: "",
        money: "",
        actionId: "",
        accountId: "",
        accountToId: "",
        typeId: "",
        dateType: "",
        tagId: "",
      },

      requestLocks: {},
    };
  },
  mounted() {
    this.getAllTags();
    this.doGetActions();
    this.doGetAccounts();
  },
  methods: {
    //路由
    toTagManage() {
      this.$router.push({path: "/template/tag"})
    },
    leftClick() {
      this.$router.go(-1);
    },


    //点击事件
    onActionClick() {
      this.actionShow = true;
      this.popupTitle = "选择账单收支";
      this.popupStyle = 0;
    },

    onChooseAction(action) {
      this.actionShow = false;
      if (action === this.chooseAction) {
        return
      }
      this.chooseAction = action;
      this.chooseAccountTo = {};
      this.chooseType = {}
      this.doGetTypes()
    },

    onTypeClick() {
      if (this.chooseAction.id == null) {
        showFailToast("请先选择收支")
        return;
      }
      this.typeCascaderShow = true;
    },

    onChooseCascader({selectedOptions}) {
      this.typeCascaderShow = false;
      this.chooseType.id = this.cascaderValue
      this.chooseType.tname = selectedOptions.map((option) => option.tname).join('/');

      console.log(this.chooseType)
    },

    onAccountClick(popupStyle) {
      this.actionShow = true;
      this.popupTitle = "选择账户";
      this.popupStyle = popupStyle;
    },

    onChooseAccount(account, popupStyle) {
      this.actionShow = false;
      if (popupStyle == 1) {
        this.chooseAccount = account
      } else {
        this.chooseAccountTo = account
      }
    },

    onDateClick() {
      showDialog({
        title: '模板账单日期',
        message: '补上月-上个月最后一天\n记本月-本月记账当天',
      }).then(() => {
        // on close
      });
    },

    onSubmit() {
      if (this.template.name == null || this.template.name === "") {
        showFailToast("请填写模板名称")
        return
      }
      showConfirmDialog({
        title: '确认',
        message: '确定提交“' + this.template.name + '”吗？'
      }).then(() => {
        this.doSubmitRequest()
      }).catch(() => {
        // on cancel
      });
    },

    doSubmitRequest() {
      this.$http({
        url: this.isEdit ? "/template/updateTemplate" : "/template/addTemplate",
        method: this.isEdit ? "put" : "post",
        data: {
          id: this.isEdit ? this.template.id : null,
          name: this.template.name,
          money: this.template.money,
          actionId: this.chooseAction.id,
          accountId: this.chooseAccount.id,
          accountToId: this.chooseAccountTo.id,
          typeId: this.chooseType.id,
          dateType: this.dateTypeStr,
          tagId: this.chooseTag.id,
        }
      }).then((response) => {
        console.log(response);
        this.$router.go(-1);
      }).catch((error) => {
        console.log(error);
      });
    },

    getAllTags() {
      this.$http({
        url: "/tag/getTags",
        method: "get",
      }).then((response) => {
        this.requestLocks.tag = true;
        if (this.isEdit) {
          this.unLockRequest()
        }
        this.allTags = response.data.data;
        console.log(this.allTags);
      }).catch((error) => {
        console.log(error);
      });
    },

    doGetActions() {
      this.$http({
        url: "/action/getAction",
        method: "get"
      }).then((response) => {
        this.requestLocks.action = true;
        if (this.isEdit) {
          this.unLockRequest()
        }
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
      }).then((response) => {
        this.requestLocks.account = true;
        if (this.isEdit) {
          this.unLockRequest()
        }
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
          }).catch((error) => {
        console.log(error);
      });
    },

    unLockRequest() {
      if (this.requestLocks.action && this.requestLocks.account && this.requestLocks.tag) {
        this.getTemplateById()
      }
    },

    getTemplateById() {

      this.$http({
        url: "/template/getTemplateById/" + this.$route.query.templateId,
        method: "get",
      }).then((response) => {
        this.template = response.data.data;
        if (this.template.actionId == null) {
          this.chooseAction = {}
        } else {
          this.chooseAction = this.allActions.find((action) => action.id === this.template.actionId);
        }

        if (this.template.accountId == null) {
          this.chooseAccount = {}
        } else {
          this.chooseAccount = this.allAccounts.find((account) => account.id === this.template.accountId);
          this.doGetTypes()
        }

        if (this.template.accountToId == null) {
          this.chooseAccountTo = {}
        } else {
          this.chooseAccountTo = this.allAccounts.find((account) => account.id === this.template.accountToId);
        }

        if (this.template.typeId == null) {
          this.chooseType = {}
        } else {
          this.chooseType.id = this.template.typeId;
          this.chooseType.tname = this.template.type.tname;
        }

        if (this.template.tagId == null) {
          this.chooseTag = {}
        } else {
          this.chooseTag = this.allTags.find((tag) => tag.id === this.template.tagId);
        }
        this.dateTypeStr = this.template.dateType == null ? "" : this.template.dateType.toString();
        console.log(this.template);
      }).catch((error) => {
        console.log(error);
      });
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

    deleteTemplate() {
      showConfirmDialog({
        title: '确认',
        message: '确定删除“' + this.template.name + '”吗？'
      }).then(() => {
        this.$http({
          url: "/template/deleteTemplate/" + this.template.id,
          method: "delete",
        }).then((response) => {
          console.log(response);
          this.$router.go(-1);
        }).catch((error) => {
          console.log(error);
        });
      }).catch(() => {
        // on cancel
      });
    },
  },

}
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
</style>