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
          v-model="tname"
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
          :title="chooseType.tname"
          @click="onShowParentPicker"
      />
      <van-cell title="绑定收支" is-link @click="onShowActionPicker">
        <template #default>
          <van-tag :type="action.style">{{ action.hname }}</van-tag>
          <van-tag
              v-show="action.exempt"
              style="margin-left: 10px"
              color="gray"
              plain
              type="action.style"
          >{{ action.value }}
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <div style="margin: 20px ">
      <van-button
          v-if="this.$route.query.editId"
          size="large"
          type="warning"
          @click="onArchiveClick"
      >
        归档
      </van-button>
      <van-button
          v-if="this.$route.query.editId"
          size="large"
          type="danger"
          @click="onDeleteClick"
          style="margin-top: 15px"
      >
        停用
      </van-button>
    </div>

    <van-popup
        v-model="showPicker"
        round
        position="bottom"

    >
      <van-picker
          title="选择一级分类"
          show-toolbar
          :cancel-button-text="cancelButtonText"
          :columns="columns"
          visible-item-count="8"
          @confirm="onParentConfirm"
          @cancel="onParentCancel"
      />

    </van-popup>
    <van-action-sheet
        cancel-text="清空绑定"
        close-on-click-action
        @cancel="clearBindAction"
        v-model="showAction" title="绑定收支">
      <van-cell-group>
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
    </van-action-sheet>
  </div>
</template>

<script>
import {Dialog, Toast} from "vant";
import request from "../../utils/request";

export default {
  computed: {
    cancelButtonText() {
      // 如果 URL 中有 editId，则取消按钮显示“清空”，否则没有文本
      return this.$route.query.editId ? "清空" : "";
    }
  },
  data() {
    return {
      tname: "",
      showPicker: false,
      showAction: false,
      action: {},
      allActions: [],
      chooseType: {},
      columns: [],
      typeList: [],
      chooseName: "",
      chooseId: 0,
      curParent: -1,
      canEditAction: true,
    };
  },
  mounted() {
    if (this.$route.query.editId) {
      this.onSingleType();
    }
  },
  methods: {
    onArchiveClick() {
      console.log("归档");
      Dialog.confirm({
        title: '归档',
        message: this.curParent===-1?'确定将此分类归档吗？\n注意，一级分类归档会连带子分类一起归档\n归档后将不再显示，但不会删除数据':'确定将此分类归档吗？\n归档后将不再显示，但不会删除数据',
      })
          .then(() => {
            request({
              url: "/type/archiveType/" + this.$route.query.typeId,
              params: {
                archive : true,
              },
              method: "put",
            }).then(() => {
              this.$router.go(-1);
            })
          })
          .catch(() => {
            // on cancel
          });
    },

    onDeleteClick() {
      Dialog.confirm({
        title: '停用',
        message: this.curParent===-1?'确定停用此分类吗？\n注意，一级分类停用会连带子分类一起停用\n停用后将无法再使用此分类':'确定停用此分类吗？\n停用后将无法再使用此分类',
      })
          .then(() => {
            request({
              url: "/type/deleteType/" + this.$route.query.typeId,
              method: "delete",
            }).then(() => {
              this.$router.go(-1);
          })
          .catch(() => {
            // on cancel
          });
      });
    },

    onChooseAction(action) {
      if (this.curParent === -1 ){
        Dialog.confirm({
          title: '注意！',
          message: '一级分类绑定收支后\n二级分类将自动同步绑定该收支\n是否继续？',
        })
            .then(() => {
              this.showAction = false;
              this.action = action;
            })
            .catch(() => {
              // on cancel
            });
      }else {
        this.showAction = false;
        this.action = action;
      }
    },

    clearBindAction() {
      this.showAction = false;
      this.action = {};
    },

    onSingleType() {
      request({
        url: "/type/getTypeSingle/" + this.$route.query.typeId,
        method: "get",
      }).then((response) => {
        console.log(response);
        this.tname = response.data.data.tname;
        this.curParent = response.data.data.parent;
        if (response.data.data.action !== null) {
          this.action = response.data.data.action;
          this.action = this.setActionStyle(this.action)
           }

        if (this.curParent !== -1) {
          request({
            url: "/type/getTypeSingle/" + response.data.data.parent,
            method: "get",
          }).then((pres) => {
            this.chooseType = pres.data.data;
            this.chooseName = pres.data.data.tname;
            if (pres.data.data.action !== null) {
              this.canEditAction = false;
            }
            console.log("父辈："+pres.data.data);
          });
        } else {
          this.chooseName = "";
        }
      });
    },

    setActionStyle(action) {
      action.value = action.exempt ? "不计入总金额" : ""
      action.handleText = action.handle === 0 ? "账户金额增加" : action.handle === 1 ? "账户金额减少" : "账户金额不变"
      action.style = action.handle === 0 ? "success" : action.handle === 1 ? "danger" : "primary"
      return action
    },

    onUpdateClick() {
      Dialog.confirm({
        title: "更新",
        message: "确定更新此分类吗？",
      })
          .then(() => {
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
                id: this.$route.query.typeId,
                tname: this.tname,
                parent: this.chooseType.id,
                actionId: this.action.id
              },
            })
                .then(() => {
                  this.$router.go(-1);
                  toast.clear();
                })
                .catch(() => {
                  toast.clear();
                });
          })
          .catch(() => {
            // on cancel
          });
    },

    getAllAction() {
      request({
        url: "/action/getAction",
        method: "get",
      }).then((response) => {
        this.allActions = response.data.data;
        this.allActions.forEach((action) => {
          this.setActionStyle(action)
        })
        console.log(this.allActions);
      }).catch((error) => {
        console.log(error);
      });
    },

    onShowActionPicker() {
      if (!this.canEditAction){
        Toast("当前分类不可绑定收支");
        return;
      }
      this.showAction = true;
      this.getAllAction();
    },

    onShowParentPicker() {
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
              this.columns[index] = item.tname;
              if (item.action != null) {
                this.setActionStyle(item.action)
              }
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

    onParentCancel() {
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
          tname: this.tname,
          parent: this.chooseType.id,
          actionId: this.action.id
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

    onParentConfirm(value, index) {
      this.showPicker = false;
      this.chooseType = this.typeList[index];
      this.chooseName = this.chooseType.tname;
      this.curParent = this.chooseType.id;
      if (this.chooseType.action !== null) {
        this.action = this.chooseType.action;
        this.canEditAction = false;
      }else {
        this.action = {};
        this.canEditAction = true;
      }
    },
  },
};
</script>

<style scoped></style>
