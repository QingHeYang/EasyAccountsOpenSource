<template>
  <div>
    <van-nav-bar
        fixed placeholder
        title="设置"/>
    <van-cell icon="exchange" title="收支" is-link to="/setting/action"/>
    <van-cell icon="paid" title="账户" is-link to="/setting/account"/>
    <van-cell icon="balance-list-o" title="分类" is-link to="/setting/type"/>
    <van-cell icon="cluster-o" title="快记模板" is-link to="/setting/template"/>
    <van-cell icon="flag-o" title="关于" @click="showAbout=true" is-link/>
    <van-cell icon="revoke" title="退出登录" @click="this.logout"/>
    <!--    <van-cell icon="more-o" title="更多" is-link to="/setting/config" />-->


    <van-dialog v-model:show="showAbout" title="关于">
      <div style="text-align: center; padding: 12px; font-family: 'Helvetica Neue', Arial, sans-serif; color: #333;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 6px;">
          <van-image
              :src="logoUrl"
              fit="contain"
              style="width: 30px; height: 30px;"
          />
          <span style="font-size: 16px; font-weight: bold;">EasyAccounts</span>
        </div>
        <!-- 第二行：副标题 -->
        <div style="margin-top: 6px; font-size: 14px; color: #666;">
          认真生活, 好好记账
        </div>
        <!-- 第三行：发行版本 -->
        <div style="margin-top: 20px; font-size: 15px; color: #333;">
          发行版本: {{ versions.release }}
        </div>
        <!-- 第四行：Powered by + 头像 + GitHub -->
        <div style="margin-top: 20px; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 4px;">
          <span style="color: #999">Powered by</span>
          <img
              src="https://avatars.githubusercontent.com/u/19968251?u=5bc82e5f642e80a6aa51c9eb10389932db38135f&amp;v=4&amp;size=64"
              alt="GitHub Avatar"
              style="width: 18px; height: 18px; border-radius: 50%;"
          />
          <a
              href="https://github.com/QingHeYang/EasyAccounts"
              target="_blank"
              style="color: #007aff; text-decoration: none;"
          >
            QingHeYang
          </a>
        </div>
      </div>
    </van-dialog>



  </div>

</template>
<script>
import logo from '@/assets/logo.png';
import {showConfirmDialog} from "vant";

export default {

  name: "Setting",
  data() {
    return {
      logoUrl: logo,
      showAbout: false,
      versions: {}
    };
  },
  mounted() {
    this.getVersion();
  },
  methods: {
    logout() {
      showConfirmDialog({
        title: '退出登录',
        message: '确定要退出登录吗？',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }).then(() => {
        this.$router.push({
          path: '/auth', // 确保路径与路由配置一致
          query: {redirect: "/", mode: 1}
        });
      }).catch(() => {
        // on cancel
      });
    },

    getVersion() {
      this.$http.get('/home/getVersion')
          .then(response => {
            this.versions = response.data.data
          }).catch(error => {
        console.error(error);
      });

    }
  }
};
</script>

<style scoped>
.powered-by {
  position: fixed; /* 固定位置 */
  bottom: 70px; /* 定位到底部 */
  width: 100%; /* 宽度为100% */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff; /* 背景颜色 */
  padding: 10px 0; /* 上下填充 */
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1); /* 添加顶部阴影 */
  font-family: 'Roboto', sans-serif;
  font-size: 12px;
  color: #666;
}

.avatar {
  width: 25px;
  height: 25px;
  border-radius: 50%;
  margin: 0 5px;
}

.powered-by a {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #666;
}
</style>
