<template>
  <div>
    <van-nav-bar
      v-if="this.$route.query.accountId != null"
      title="添加账号"
      left-text="返回"
      right-text="更新"
      left-arrow
      @click-left="onClickLeft"
      @click-right="onClickRight"
    />

    <van-nav-bar
      v-else
      title="添加账号"
      left-text="返回"
      right-text="保存"
      left-arrow
      @click-left="onClickLeft"
      @click-right="onClickRight"
    />

    <van-cell-group>
      <van-field
        v-model="aName"
        label="账号名称"
        required
        placeholder="请输入账号名称"
      />
      <van-field
        v-model="money"
        type="number"
        label="账户余额"
        required
        placeholder="请输入账户余额"
      />
      <van-field
        v-model="exempt"
        type="number"
        label="豁免金额"
        placeholder="请输入账户余额中不计入总金额的钱数"
      />
      <van-field v-model="card" label="银行卡号" placeholder="请输入银行卡号" />

      <van-field
        v-model="note"
        rows="3"
        autosize
        label="账户信息备注"
        type="textarea"
        maxlength="50"
        placeholder="请输入备注"
        show-word-limit
      />
    </van-cell-group>
  </div>
</template>

<script>
// import { Toast } from 'vant';
import { Toast } from "vant";
import { Notify } from "vant";
import request from "../../utils/request";

export default {
  data() {
    return {
      aName: "",
      card: "",
      money: "",
      exempt: "",
      note: ""
    };
  },
  mounted() {
    if (this.$route.query.accountId != null) {
      this.getAccountSingle();
    }
  },

  methods: {
    getAccountSingle() {
      request({
        url: "/account/getAccount/" + this.$route.query.accountId,
        method: "get"
      }).then((respons) => {
        const account = respons.data.data;
        console.log(account);
        this.aName = account.name;
        this.card = account.card;
        this.exempt = account.exemptMoney;
        this.note = account.note;
        this.money = account.money;
      });
    },

    onClickLeft() {
      this.$router.go(-1);
    },

    doAdd() {

      const toast = Toast.loading({
        message: "保存中...",
        duration: 0,
        forbidClick: true,
        loadingType: "spinner"
      });
      request({
        url: "/account/addAccount",
        method:"post",
        data: {
          name: this.aName,
          money: this.money,
          card: this.card,
          exemptMoney: this.exempt,
          note: this.note
        }
      })
        .then((response) => {
          toast.clear();
          Notify({ type: "success", message: "保存成功" });
          this.$router.go(-1);
          console.log(response.data);
        })
        .catch((error) => {
          toast.clear();
         // Notify({ type: "danger", message: "保存失败" });
          console.log(error);
        });
    },

    doUpdate() {
      const toast = Toast.loading({
        message: "更新中...",
        duration: 0,
        forbidClick: true,
        loadingType: "spinner"
      });
      request({
        url: "/account/updateAccount/"+this.$route.query.accountId,
        method:"put",
        data: {
          name: this.aName,
          money: this.money,
          card: this.card,
          exemptMoney: this.exempt,
          note: this.note
        }
      })
        .then(() => {
          toast.clear();
          Notify({ type: "success", message: "更新成功" });
          this.$router.go(-1);
        })
        .catch((error) => {
          toast.clear();
          Notify({ type: "danger", message: "更新失败" ,duration:600});
          console.log(error);
        });
    },

    onClickRight() {
      /* */
      if (this.aName === "") {
        Toast.fail("账号名为空");
        return;
      }
      if (this.money === "") {
        Toast.fail("初始金额为空");
        return;
      }
      if (parseInt(this.exempt)>parseInt(this.money)){
        Toast.fail("不计入总金额钱数不得大于账户余额")
        return
      }
      if (this.$route.query.accountId != null) {
        this.doUpdate();
      } else {
        this.doAdd();
      }
    }
  }
};
</script>

<style scoped></style>
