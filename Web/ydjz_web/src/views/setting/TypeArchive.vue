<template>
  <div style="width:100vw; height:100vh; background: #F7F8FA">
    <van-nav-bar
        title="管理归档"
        left-arrow
        fixed placeholder
        @click-left="onClickLeft"
    />

    <van-cell-group  inset :border="false" :style="{marginTop:'10px',background:'#F7F8FA'}" v-for="item in allArchive" :key="item.id">
      <van-collapse :border="false" v-model="activeNames" >
        <van-collapse-item  :name="item.id" :title="item.tname">
          <template v-if="item.action!=null" #value>
            <van-tag >{{ item.action.hname }}</van-tag>
          </template>
          <div
              style="right: 10px; color: cornflowerblue; font-size: 12px"
              @click="onDisableArchiveClick(item)"
          >
            {{item.parent!=-1?"二级分类":"一级分类"}} 取出归档
          </div>
          <van-cell
              v-for="child in item.childrenTypes"
              :key="child.id"
              @click="showToast('归档时无法编辑')"
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
import {showConfirmDialog, showToast} from "vant";

export default {
  data() {
    return {
      list: [],
      error: false,
      loading: false,
      activeNames: [],
      allArchive: [],
    };
  },
  mounted() {
    this.getAllArchive()
  },
  methods: {
    onClickLeft() {
      this.$router.go(-1);
    },

    showToast(message) {
      showToast(message);
    },

    onDisableArchiveClick(type) {
      var msg = ""
      if (type.parent!=-1){
        msg = "该分类为：二级分类\n确定取出“"+type.tname+"”吗？\n二级分类取出后，会回到一级分类中"
      }else {
        msg = "该分类为：一级分类\n确定取出“"+type.tname+"”吗？\n一级分类取出后，下属二级分类会一同取出"
      }
      showConfirmDialog({
        title: "提示",
        message: msg,
      })
          .then(() => {
            this.$http({
              url: "/type/archiveType/" + type.id,
              params: {
                archive : false,
              },
              method: "put",
            }).then(() => {
              this.showToast("取出成功")
              this.getAllArchive();
            }).catch((error) => {
              console.log(error);
            });
          })
          .catch(() => {
            // on cancel
          });

    },

    getAllArchive() {
      this.$http({
        url: "/type/getTypeArchive",
        method: "get",
      }).then((response) => {
        this.allArchive = response.data.data;
        console.log(this.list);
      }).catch((error) => {
        console.log(error);
      });
    },
  },
};

</script>


<style scoped>

</style>