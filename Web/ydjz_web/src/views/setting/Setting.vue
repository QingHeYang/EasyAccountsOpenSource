<template>
  <div>
    <van-nav-bar
        fixed placeholder
      title="设置" />
    <van-cell icon="exchange" title="收支" is-link to="/setting/action" />
    <van-cell icon="paid" title="账户" is-link to="/setting/account" />
    <van-cell icon="balance-list-o" title="分类" is-link to="/setting/type" />
    <van-cell icon="cluster-o" title="快记模板" is-link to="/setting/template" />

    <!-- 新增 Powered by 区域 -->
    <div class="powered-by">
      <span>Powered by </span>
      <a href="https://github.com/QingHeYang/EasyAccounts" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/19968251?u=5bc82e5f642e80a6aa51c9eb10389932db38135f&amp;v=4&amp;size=32" alt="GitHub Avatar" class="avatar">
        <span>QingHeYang</span>
      </a>
    </div>
  </div>

</template>
<script>
export default {};
</script>

<style scoped>
.powered-by {
  position: fixed;  /* 固定位置 */
  bottom: 70px;        /* 定位到底部 */
  width: 100%;      /* 宽度为100% */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff; /* 背景颜色 */
  padding: 10px 0;  /* 上下填充 */
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
