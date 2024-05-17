<template>
  <div>
    <van-nav-bar
      title="分类"
      left-arrow
      right-text="添加"
      @click-left="onClickLeft"
      @click-right="onClickRight"
    >
    </van-nav-bar>
    <van-collapse v-model="activeNames">
      <van-collapse-item
        :name="item.id"
        v-for="item in list"
        :key="item.id"
        :title="item.tName"
      >
        <div
          style="right: 10px; color: cornflowerblue; font-size: 10px"
          @click="onEditClick(item.id)"
        >
          编辑一级分类
        </div>
        <van-cell
          v-for="child in item.childrenTypes"
          :key="child.id"
          :title="child.tName"
        >
          <div
            style="color: cornflowerblue; font-size: 10px"
            @click="onEditClick(child.id)"
          >
            编辑
          </div>
        </van-cell>
      </van-collapse-item>
    </van-collapse>
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
    onEditClick(id) {
      this.$router.push({
        path: "/type/add",
        query: { typeId: id, editId: true },
      });
    },
    onLoad() {
      request({
        url: "/type/getType",
        method: "get",
      })
        .then((response) => {
          this.loading = false;
          this.list = response.data.data;
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
