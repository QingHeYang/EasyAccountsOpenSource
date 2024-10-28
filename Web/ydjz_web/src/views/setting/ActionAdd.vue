<template>
  <div>
    <van-nav-bar
      v-if="this.$route.query.action != null"
      title="修改操作"
      left-arrow
      @click-left="onClickLeft"
    />
    <van-nav-bar v-else title="添加操作" left-arrow @click-left="onClickLeft" />
    <van-cell-group>
      <van-field
        v-model="actionName"
        label="账户操作"
        placeholder="请输入账户操作名称"
      />
      <van-field name="radio" label="单选框">
        <template #input>
          <van-radio-group v-model="radio" direction="vertical">
            <van-radio name="0">账户金额增加</van-radio>
            <van-radio style="margin-top: 10px" name="1"
              >账户金额减少</van-radio
            >
            <van-radio style="margin-top: 10px" name="2"
              >账户金额不变</van-radio
            >
          </van-radio-group>
        </template>
      </van-field>

      <van-field name="switch" label="不计入总金额">
        <template #input>
          <van-switch v-model="switchChecked" size="20" />
        </template>
      </van-field>
    </van-cell-group>
    <div style="margin: 16px">
      <van-button @click="onSubmit" round block type="info" native-type="submit"
        >{{ this.$route.query.action != null ? "完成修改" : "添加" }}
      </van-button>
    </div>
  </div>
</template>

<script>
import request from "../../utils/request";
import { Toast } from "vant";

export default {
  name: "ActionAdd",
  data() {
    return {
      actionName: "",
      radio: "0",
      switchChecked: false,
    };
  },
  mounted() {
    if (this.$route.query.action != null) {
      this.getAction();
    }
  },
  methods: {
    getAction() {
      request({
        url: "/action/getAction/" + this.$route.query.action,
      }).then((res) => {
        const action = res.data.data;
        this.actionName = action.hname;
        this.radio = action.handle + "";
        this.switchChecked = action.exempt;
        console.log(action);
      });
    },

    onSubmit() {
      const toastMsg =
        this.$route.query.action == null ? "添加中..." : "修改中...";
      const toast = Toast.loading({
        message: toastMsg,
        duration: 0,
        forbidClick: true,
        loadingType: "spinner",
      });
      const api =
        this.$route.query.action == null
          ? "/action/addAction"
          : "/action/updateAction/" + this.$route.query.action;
      const method = this.$route.query.action == null ? "post" : "put";
      request({
        url: api,
        method: method,
        data: {
          hname: this.actionName,
          handle: parseInt(this.radio),
          exempt: this.switchChecked,
        },
      })
        .then(() => {
          toast.clear();
          this.$router.go(-1);
        })
        .catch(() => {
          toast.clear();
        });
    },

    onClickLeft() {
      this.$router.go(-1);
    },
  },
};
</script>

<style scoped></style>
