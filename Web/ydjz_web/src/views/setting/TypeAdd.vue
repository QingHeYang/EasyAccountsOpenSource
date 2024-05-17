<template>
  <div>
    <van-nav-bar
      title="添加分类"
      left-text="返回"
      v-if="this.$route.query.editId"
      right-text="更新"
      left-arrow
      @click-left="onClickLeft"
      @click-right="onUpdateClick"
    />

    <van-nav-bar
      v-else
      title="添加分类"
      left-text="返回"
      right-text="保存"
      left-arrow
      @click-left="onClickLeft"
      @click-right="onClickRight"
    />
    <van-cell-group>
      <van-field
        v-model="tName"
        label="分类名称"
        required
        placeholder="请输入分类名称"
      />
      <van-field
        v-model="chooseName"
        is-link
        readonly
        label="父级分类"
        placeholder="请选择一级分类"
        :title="chooseType.tName"
        @click="onShowPicker"
      />
    </van-cell-group>

    <van-button
      v-if="this.$route.query.editId"
      size="large"
      hairline
      type="warning"
      style="padding: 20px; margin-top: 30px"
    >
      删除
    </van-button>
    <van-popup
      v-model="showPicker"
      round
      position="bottom"
      :style="{ height: '30%' }"
    >
      <van-picker
        v-if="this.$route.query.editId"
        title="选择一级分类"
        show-toolbar
        cancel-button-text="清空"
        :columns="columns"
        @confirm="onConfirm"
        @cancel="onCancel"
      />
      <van-picker
        v-else
        title="选择一级分类"
        show-toolbar
        :columns="columns"
        @confirm="onConfirm"
        @cancel="onCancel"
      />
    </van-popup>
  </div>
</template>

<script>
import { Toast } from "vant";
import request from "../../utils/request";

export default {
  data() {
    return {
      tName: "",
      showPicker: false,
      chooseType: {},
      columns: [],
      typeList: [],
      chooseName: "",
      chooseId: 0,
      curParent: -1,
    };
  },
  mounted() {
    if (this.$route.query.editId) {
      this.onSingleType();
    }
  },
  methods: {
    onSingleType() {
      request({
        url: "/type/getTypeSingle/" + this.$route.query.typeId,
        method: "get",
      }).then((response) => {
        console.log(response);
        this.tName = response.data.data.tName;
        this.curParent = response.data.data.parent;
        if (this.curParent !== -1) {
          request({
            url: "/type/getTypeSingle/" + response.data.data.parent,
            method: "get",
          }).then((pres) => {
            this.chooseType = pres.data.data;
            this.chooseName = pres.data.data.tName;
          });
        } else {
          this.chooseName = "";
        }
      });
    },

    onUpdateClick() {
      const toast = Toast.loading({
        message: "更新中...",
        forbidClick: true,
        duration: 0,
        loadingType: "spinner",
      });
      request({
        url: "/type/updateType/" + this.$route.query.typeId,
        method: "put",
        data: {
          tName: this.tName,
          parent: this.chooseType.id,
        },
      })
        .then(() => {
          this.$router.go(-1);
          toast.clear();
        })
        .catch(() => {
          toast.clear();
        });
    },

    onShowPicker() {
      if (this.$route.query.editId) {
        if (this.curParent === -1) {
          Toast("当前已经是一级分类了");
          return;
        }
      }
      request({
        url: "/type/getType/-1",
        method: "get",
      })
        .then((response) => {
          this.typeList = response.data.data;
          this.typeList.forEach((item, index) => {
            this.columns[index] = item.tName;
          });
          this.showPicker = true;
        })
        .catch((err) => {
          console.log(err);
        });
    },
    onClickLeft() {
      this.$router.go(-1);
    },

    onCancel() {
      if (this.$route.query.editId) {
        this.chooseType.id = -1;
        this.chooseName = "";
      }
      this.showPicker = false;
    },
    onClickRight() {
      const toast = Toast.loading({
        message: "保存中...",
        forbidClick: true,
        duration: 0,
        loadingType: "spinner",
      });
      request({
        url: "/type/addType",
        method: "post",
        data: {
          tName: this.tName,
          parent: this.chooseType.id,
        },
      })
        .then(() => {
          this.$router.go(-1);
          toast.clear();
        })
        .catch(() => {
          toast.clear();
        });
    },

    onConfirm(value, index) {
      this.showPicker = false;
      this.chooseType = this.typeList[index];
      this.chooseName = this.chooseType.tName;
    },
  },
};
</script>

<style scoped></style>
