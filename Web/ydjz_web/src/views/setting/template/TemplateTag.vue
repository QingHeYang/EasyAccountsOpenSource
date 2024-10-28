<template>
  <div>
    <van-nav-bar
        title="标签管理"
        left-arrow
        @click-left="leftClick"
    >
    </van-nav-bar>

    <van-divider
        :style="{ color: '#1989fa', borderColor: '#1989fa', padding: '0 16px' }"
    > 全部标签
    </van-divider>
    <!--    <van-grid v-if="allTags.length!==0" :border="false" :column-num="4">
          <van-grid-item v-for="tag in allTags" :key="tag.id" @click="onEdit(tag)">
            <template #default>
              <van-tag size="large" :color="tag.color">{{ tag.name }}</van-tag>
            </template>
          </van-grid-item>
        </van-grid>-->

    <div v-if="allTags.length !== 0" class="tags-container">
      <div class="tag-item" v-for="tag in allTags" :key="tag.id"
           @click="onEdit(tag)">
        <van-tag size="large" :color="tag.color">{{ tag.name }}</van-tag>
      </div>
    </div>
    <van-empty v-else description="当前无标签"/>
    <div style="padding: 30px">
      <van-button type="primary" @click="newPopupShow=true;isEdit = false" block size="large">新建标签</van-button>
    </div>

    <van-popup title="选择标签" round closeable v-model="newPopupShow"
               @close="newPopupShow=false,usedName='',usedColor=''"
               :style="{background:'#F7F8FA', height: '70%',width:'75%',padding:'10px' }">
      <div style="text-align: center; color: #333; font-size: 16px; margin-top: 10px">
        {{ isEdit ? '修改标签' : '新建标签' }}
      </div>
      <van-cell-group :style="{marginTop:'15px'}" inset :border="false">
        <van-field label="名称" v-model="usedName"
                   placeholder="请输入标签名"
                   clearable maxlength="4"/>
      </van-cell-group>

      <van-cell-group inset :border="false" :style="{marginTop:'15px'}">
        <van-cell title="颜色">
          <template #default>
            <van-tag size="medium" v-if="usedName!=''&&usedColor!='' " :color="usedColor">
              {{ usedName }}
            </van-tag>
          </template>
        </van-cell>
        <van-grid :border="false" :column-num="6">
          <van-grid-item v-for="item in tag_colors" :key="item.id" @click="usedColor = item.color">
            <template #default>
              <div
                  :style="{ background: item.color, height: '20px', width: '100%', display: 'block', borderRadius: '8px' }"/>
            </template>
          </van-grid-item>
        </van-grid>
      </van-cell-group>
      <div style="margin: 20px">
        <van-button size="large" type="info" @click="isEdit?updateTag():addNewTag()">{{ isEdit ? "修改" : "新建" }}
        </van-button>
        <van-button v-if="isEdit" size="large" type="danger" style="margin-top: 10px" @click="deleteTag">删除
        </van-button>
      </div>
    </van-popup>
  </div>

</template>
<script>
import request from "../../../utils/request";
import {Dialog} from "vant";

export default {
  name: "TemplateTag.vue",
  mounted() {
    this.getAllTags();
  },
  data() {
    return {
      newPopupShow: false,
      isEdit: false,
      allTags: [],
      chooseTag: {
        id: null,
        name: "",
        color: "",
      },

      usedName: "",
      usedColor: "",

      tag_colors: [
        //{id: 1, color: "#FFF8DC"}, // 浅黄
        {id: 2, color: "#FFEA00"}, // 中黄
        {id: 3, color: "#ECD540"}, // 金黄
        {id: 4, color: "#B8860B"},
        {id: 5, color: "#90EE90"}, // 浅绿
        {id: 6, color: "#3CB371"}, // 蓝绿
        {id: 7, color: "#008000"}, // 绿色
        {id: 8, color: "#006400"}, // 深绿
        {id: 9, color: "#013220"}, // 墨绿
        {id: 10, color: "#FFCCB6"}, // 浅粉
        {id: 11, color: "#FFB6C1"}, // 粉红
        {id: 12, color: "#FF1493"}, // 深粉
        {id: 13, color: "#FFA500"}, // 橘黄
        {id: 14, color: "#FF4500"}, // 橘红
        {id: 15, color: "#D2B48C"}, // 浅棕
        {id: 16, color: "#8B4513"}, // 深棕
        {id: 17, color: "#ADD8E6"}, // 浅蓝
        {id: 18, color: "#48D1CC"}, // 蓝色
        {id: 19, color: "#120A8F"}, // 深蓝
        {id: 20, color: "#000080"}, // 墨蓝
        {id: 21, color: "#B57EDC"}, // 浅紫
        {id: 22, color: "#800080"}, // 紫色
        {id: 23, color: "#4B0082"}, // 深紫
        //{id: 24, color: "#2E0854"}, // 黑紫
        {id: 25, color: "#FFA07A"}, // 浅红
        {id: 26, color: "#FF0000"}, // 红色
        {id: 27, color: "#8B0000"}, // 深红
        {id: 28, color: "#800020"}, // 酒红
        {id: 29, color: "#600000"}, // 墨红
        {id: 30, color: "#A9A9A9"}, // 深灰
        {id: 31, color: "#607B8B"}, // 蓝灰
        {id: 32, color: "#000000"}  // 黑色
      ]
    }

  },
  methods: {
    leftClick() {
      this.$router.go(-1);
    },

    onEdit(tag) {
      this.chooseTag = tag
      this.usedName = tag.name
      this.usedColor = tag.color
      this.isEdit = true
      this.newPopupShow = true
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

    addNewTag() {
      if (this.usedName === "" || this.usedColor === "") {
        this.$toast.fail("请填写完整信息");
        return;
      }
      request({
        url: "/tag/addTag",
        method: "post",
        data: {
          name: this.usedName,
          color: this.usedColor,
        },
      }).then((response) => {
        console.log(response);
        this.newPopupShow = false;
        this.getAllTags()
      }).catch((error) => {
        console.log(error);
      });
    },

    updateTag() {
      if (this.chooseTag.name === "" || this.chooseTag.color === "") {
        this.$toast.fail("请填写完整信息");
        return;
      }
      request({
        url: "/tag/updateTag",
        method: "put",
        data: {
          id: this.chooseTag.id,
          name: this.usedName,
          color: this.usedColor,
        },
      }).then((response) => {
        console.log(response);
        this.newPopupShow = false;
        this.getAllTags()
      }).catch((error) => {
        console.log(error);
      });
    },

    deleteTag() {
      Dialog.confirm({
        title: '删除',
        message: '确定删除此标签吗？\n删除后模板中的标签将一并删除',
      }).then(() => {
        request({
          url: "/tag/deleteTag/" + this.chooseTag.id,
          method: "delete",
        }).then((response) => {
          console.log(response);
          this.newPopupShow = false;
          this.getAllTags()
        }).catch((error) => {
          console.log(error);
        });
      }).catch(() => {
        console.log("cancel");
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