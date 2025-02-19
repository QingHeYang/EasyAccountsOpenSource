<template>
  <div>
    <van-config-provider :theme="theme">
      <van-nav-bar
          fixed placeholder

          title="配置项"/>

      <van-cell-group>
        <van-cell title="启用登录">
          <template #right-icon>
            <van-switch v-model="enableLogin" @click="onDarkModeChange" size="24px"/>
          </template>
        </van-cell>
        <van-cell title="暗黑模式">
          <template #right-icon>
            <van-switch v-model="useDarkMode" @click="onDarkModeChange" size="24px"/>
          </template>
        </van-cell>
        <van-cell title="版本号" value="中" is-link/>
        <van-cell title="清除缓存" value="0.0B" is-link/>
        <van-cell title="关于" is-link/>
      </van-cell-group>

      <!-- 新增 Powered by 区域 -->
      <div class="powered-by">
        <span>Powered by </span>
        <a href="https://github.com/QingHeYang/EasyAccounts" target="_blank">
          <img
              src="https://avatars.githubusercontent.com/u/19968251?u=5bc82e5f642e80a6aa51c9eb10389932db38135f&amp;v=4&amp;size=32"
              alt="GitHub Avatar" class="avatar">
          <span>QingHeYang</span>
        </a>
      </div>
    </van-config-provider>
  </div>
</template>

<script>
export default {
  name: 'Config',
  data() {
    return {
      useDarkMode: false,
      enableLogin: false,
      show: false,
    };
  },
  methods: {
    // 返回上一页
    onClickLeft() {
      this.$router.go(-1);
    },
    onDarkModeChange() {
      console.log('onDarkModeChange');
    },
    enableLoginChange() {
      console.log('enableLoginChange');
    }
  },
  computed: {
    theme() {
      // 根据 useDarkMode 的状态动态切换主题
      return this.useDarkMode ? 'dark' : 'light';
    }
  },
};
</script>


<style scoped>

</style>