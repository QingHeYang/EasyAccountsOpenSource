<template>
  <div style="width:100vw; height:100vh; background: #F7F8FA">
    <van-nav-bar  fixed placeholder
                  title="快记模板"
        left-arrow
        right-text="添加模板"
        @click-left="leftClick"
        @click-right="onClickRight"
    >
    </van-nav-bar>
    <!--  <van-button @click="toTagManage">标签管理</van-button>-->
<!--    <van-cell  title="标签筛选" is-link @click="tagManageShow=true" >
      <template #default>
        <van-tag v-if="chooseTag.id!=null"  :color="chooseTag.color" closeable @close="chooseTag = {};getAllTemplate()">{{ chooseTag.name }}</van-tag>
      </template>
    </van-cell>-->
    <van-collapse :border="false" v-model="activeNames" accordion>
      <van-collapse-item title="标签筛选" :toggle="chooseTag" name="1">
        <template #value>
          <van-tag v-if="chooseTag.id!=null" :color="chooseTag.color" closeable
                   @close="chooseTag = {};getAllTemplate()">{{ chooseTag.name }}
          </van-tag>
        </template>
        <div v-if="allTags.length !== 0" class="tags-container">
          <div class="tag-item" v-for="tag in allTags" :key="tag.id"
               @click="chooseTag = tag;getAllTemplate();">
            <van-tag size="medium" :color="tag.color">{{ tag.name }}</van-tag>
          </div>
        </div>
        <van-empty v-else description="暂无标签" style="margin-top: 10px"/>

      </van-collapse-item>
    </van-collapse>
    <div v-if="allTemplates.length>0">
    <van-cell-group  inset :border="false" :style="{marginTop:'10px'}" v-for="template in allTemplates" :key="template.id">
      <van-collapse :border="false" accordion v-model="template.show">
        <van-collapse-item :title="template.name"  name="1" >
          <template #value>
            <div style="display: flex; justify-content: flex-end;">
              <div v-if="template.tag">
                <van-tag :color="template.tag.color" style="margin-right: 15px">{{template.tag.name}}</van-tag>
              </div>
              <div
                  style="color: cornflowerblue; font-size: 14px; margin-right: 8px; cursor: pointer;"
                  @click="onEditClick(template.id)">
                编辑
              </div>
            </div>
          </template>
          <van-cell v-if="template.money"  title="金额" :value="template.money" />
          <van-cell v-if="template.actionId"  title="收支"  >
            <template #default>
              <van-tag plain :type="template.action.style">{{ template.action.hname }}</van-tag>
            </template>
          </van-cell>
          <van-cell v-if="template.accountId"  title="账户" :value="template.account.name" />
          <van-cell v-if="template.accountToId"  title="目标账户" :value="template.accountTo.name" />
          <van-cell v-if="template.typeId"  title="分类选择" :value="template.type.tname" />
          <van-cell v-if="template.dateTypeStr"  title="日期类型" :value="template.dateTypeStr==='1'?'补上月':'记本月'" />
        </van-collapse-item>
      </van-collapse>
    </van-cell-group>
    </div>
    <van-empty v-else  description="当前无模板"/>
  </div>
</template>

<script>
import request from "../../../utils/request";
import {Toast} from "vant";

export default {
  name: "Template.vue",
  data() {
    return {
      activeNames: ['1'],
      tagManageShow: false,
      allTemplates: [],
      chooseColor: "",
      allTags: [],
      chooseTag:{},
    };
  },

  mounted() {
    this.getAllTags();
    this.getAllTemplate();
  },

  methods: {
    leftClick() {
      this.$router.go(-1);
    },
    onClickRight() {
      this.$router.push({path: "/template/add"})
    },

    onEditClick(id) {
      this.$router.push({path: "/template/add", query: {templateId: id}});
    },

    getAllTemplate() {
      request({
        url: this.chooseTag.id!=null? "/template/getAllTemplatesByTag/"+this.chooseTag.id : "/template/getAllTemplates",
        method: "get",
      }).then((response) => {
        this.allTemplates = response.data.data;
        this.allTemplates.forEach((template) => {
          if (template.action){
            template.action = this.setActionStyle(template.action);
          }
          if (template.dateType!=null){
            template.dateTypeStr = template.dateType.toString();
          }else {
            template.dateTypeStr = "";
          }
        });
        console.log(this.allTemplates);
      }).catch((error) => {
        console.log(error);
      });
    },

    getAllTags() {
      request({
        url: "/tag/getTags",
        method: "get",
      }).then((response) => {
        this.allTags = response.data.data;

        console.log(this.allTags);
      }).catch((error) => {
        console.log(error);
      });
    },

    setActionStyle(action) {
      action.value = action.exempt ? "不计入总金额" : ""
      action.handleText = action.handle === 0 ? "账户金额增加" : action.handle === 1 ? "账户金额减少" : "账户金额不变"
      action.style = action.handle === 0 ? "success" : action.handle === 1 ? "danger" : "primary"
      return action
    },

    showLoading() {
      Toast.loading({
        message: '加载中...',
        forbidClick: true,
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