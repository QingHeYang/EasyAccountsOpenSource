<template>
  <div style="width:100vw; height:100vh; background: #F7F8FA">
    <van-nav-bar
        title="分类"
        left-arrow
        fixed placeholder
        right-text="添加"
        @click-left="onClickLeft"
        @click-right="onClickRight"
    >
    </van-nav-bar>
    <van-cell  title="管理归档" is-link  @click="onClickArchive" />
    <van-cell-group  inset :border="false" :style="{marginTop:'10px',background:'#F7F8FA'}" v-for="item in list" :key="item.id">
    <van-collapse :border="false" v-model="activeNames" >
      <van-collapse-item  :name="item.id" :title="item.tname">
        <template v-if="item.action!=null" #value>
          <van-tag :type="item.action.style">{{ item.action.hname }}</van-tag>
        </template>
        <div
            style="right: 10px; color: cornflowerblue; font-size: 12px"
            @click="onEditClick(item.id)"
        >
          编辑一级分类
        </div>
        <van-cell
            v-for="child in item.childrenTypes"
            :key="child.id"
            @click="onEditClick(child.id)"
            :title="child.tname"
            title-style="font-size: 12px; "
        >
          <template  v-if="child.action!=null"  #default>
            <van-tag :type="child.action.style">{{ child.action.hname }}</van-tag>
          </template>

        </van-cell>
      </van-collapse-item>
    </van-collapse>
    </van-cell-group>
  </div>
</template>

<script>
import request from "../../utils/request";

export default {
  data() {
    return {
      list: [],
      error: false,
      loading: false,
      activeNames: [],
    };
  },
  mounted() {
    this.onLoad();
  },
  methods: {
    onClickLeft() {
      this.$router.go(-1);
    },
    onClickRight() {
      this.$router.push("/type/add");
    },

    onClickArchive() {
      this.$router.push("/type/archive");
    },

    onEditClick(id) {
      this.$router.push({
        path: "/type/add",
        query: {typeId: id, editId: true},
      });
    },
    onLoad() {
      request({
        url: "/type/getType",
        method: "get",
      })
          .then((response) => {
            this.loading = false;
            var origin_list = response.data.data;
            console.log(this.list)
            origin_list.forEach((item) => {
              if (item.action!=null) {
                item.action.style = item.action.handle === 0 ? "success" : item.action.handle === 1 ? "danger" : "primary";
              }
              if (item.childrenTypes != null) {
                item.childrenTypes.forEach((child) => {
                  if (child.action!=null) {
                    child.action.style = child.action.handle === 0 ? "success" : child.action.handle === 1 ? "danger" : "primary";
                  }
                });
              }
            });
            this.list = origin_list;
          })
          .catch(() => {
            this.loading = false;
            this.finished = true;
            this.error = true;
          });
    },
  },
};
</script>

<style scoped></style>
