<template>
  <div>
    <van-nav-bar
      title="账号"
      left-arrow
      right-text="添加账号"
      @click-left="onClickLeft"
      @click-right="onClickRight"
    >
    </van-nav-bar>
    <!-- <van-empty description="暂无账号"></van-empty>-->
    <van-list
      v-model="loading"
      :finished="finished"
      finished-text="没有更多了"
      :error.sync="error"
      error-text="请求失败，点击重新加载"
      @load="onLoad"
    >
      <van-cell
        v-for="item in list"
        :key="item.id"
        :title="item.name"
        is-link
        @click="onItemClick(item)"
      />
    </van-list>

    <van-action-sheet
      v-model="showPopup"
      :title="chooseItem.name"
      close-on-click-action
    >
      <van-cell-group>
        <van-cell title="账户余额" :value="chooseItem.money" />
        <van-cell
          title="豁免金额"
          :value="chooseItem.exemptMoney"
          label="此金额包含在账户余额中"
        />
        <van-cell title="卡号" :value="chooseItem.card" />
        <van-cell title="账户备注" :value="chooseItem.note" />
      </van-cell-group>
      <div style="height: 10px; background: #f8f9fc" />
      <div id="edit" @click="onEdit(chooseItem.id)">编辑账号</div>
      <div id="delete" @click="onDelete(chooseItem.id)">删除账号</div>
    </van-action-sheet>
  </div>
</template>

<script>
import { Dialog } from "vant";
import request from "../../utils/request";

export default {
  data() {
    return {
      showPopup: false,
      list: [],
      loading: false,
      finished: false,
      chooseItem: {},
      error: false,
    };
  },

  mounted() {},

  methods: {
    onEdit(id) {
      this.$router.push({ path: "/account/add", query: { accountId: id } });
    },
    onDelete(id) {
      this.showPopup = false;

      Dialog.confirm({
        title: "删除账户",
        message: "确定删除账户吗？删除后将无法在此账户下记账",
        beforeClose,
      });

      function beforeClose(action, done) {
        if (action === "confirm") {
          request({
            url: "/account/deleteAccount/" + id,
            method: "delete",
          })
            .then((response) => {
              console.log(response.data)
              this.mounted();
            /*  if (response.data.code == 0) {
              }*/
              done();
            })
            .catch(() => {
              done();
            });
        } else {
          done();
        }
      }
    },

    onItemClick(item) {
      this.showPopup = true;
      this.chooseItem = item;
      if (item.exemptMoney === "￥") {
        this.chooseItem.exemptMoney = "未设置豁免金额";
      }
      if (item.card === "") {
        this.chooseItem.card = "未设置账户卡号";
      }
      if (item.note === "" || item.note == null) {
        this.chooseItem.note = "暂无备注";
      }
    },
    onClickLeft() {
      this.$router.go(-1);
    },
    onClickRight() {
      this.$router.push({ path: "/account/add" });
    },
    onReload(){
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
          this.list = baseData;
          console.log(this.list);
          this.finished = true;
          this.loading = false;
          this.error = false;
        })
        .catch((error) => {
          console.log(error);
          this.finished = true;
          this.loading = false;
          this.error = true;
        });
    },
    onLoad() {
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
          this.list = baseData;
          console.log(this.list);
          this.finished = true;
          this.loading = false;
          this.error = false;
        })
        .catch((error) => {
          console.log(error);
          this.finished = true;
          this.loading = false;
          this.error = true;
        });
    },
  },
};
</script>

<style>
#edit {
  height: 50px;
  background: #fff;
  color: cornflowerblue;
  font-size: 16px;
  text-align: center;
  margin: 0 15px 0 15px;
  line-height: 50px;
  border-bottom: 0.5px solid #e3e3e3;
}

#delete {
  height: 50px;
  background: #fff;
  color: #e03333;
  font-size: 16px;
  text-align: center;
  line-height: 50px;
  border-bottom: gray;
  border-width: 1px;
}
</style>
