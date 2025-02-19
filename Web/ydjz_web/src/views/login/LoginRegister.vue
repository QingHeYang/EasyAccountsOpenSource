<template>
  <div class="login-register-container">
    <div class="header-container">
      <!-- 上面一行：图片和标题 -->
      <div class="logo-title">
        <van-image
            class="logo"
            width="60px"
            height="60px"
            fit="contain"
            :src="logoUrl"
        />
        <span class="title">EasyAccounts</span>
      </div>
      <!-- 下一行：副标题 -->
      <p class="subtitle">Live slow, track flow.</p>
    </div>

    <label style="margin-top: 80px;margin-left: 20px;font-size: 24pt;margin-bottom: 15px">{{
        showNoticeTitle()
      }}</label>
    <van-form @submit="onSubmit">
      <van-cell-group inset>

        <van-field
            v-model="username"
            name="username"
            label="用户名"
            placeholder="请输入用户名"
            required
            :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
            v-model="password"
            name="password"
            label="密码"
            type="password"
            placeholder="请输入密码"
            required
            :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      <div style="display: flex;justify-content: end;margin-right: 10px;margin-top: 5px">
        <a style="color: #1989fa" @click="onForgotPassword">忘记密码？</a>
      </div>
      <div class="button-group">
        <van-button type="success" block native-type="submit">
          {{ mode === "1" ? '登录' : '注册' }}
        </van-button>

      </div>
    </van-form>

  </div>
</template>

<script>
import {showDialog} from "vant";
import logo from '@/assets/logo.png';
import MD5 from 'crypto-js/md5'
export default {

  name: "LoginRegister",
  data() {
    return {
      logoUrl: logo,
      username: "",
      password: "",
      mode: this.$route.query.mode,
    };
  },
  mounted() {
    localStorage.removeItem("token");
  },
  methods: {
    showNoticeTitle() {
      if (this.mode === '1') {
        return '请登录';
      } else if (this.mode === '0') {
        return '请注册';
      }
    },
    onSubmit() {
      const username = this.username.trim();
      const password = this.password.trim();
      let msg = '';

      if (username.length < 3) {
        msg = '用户名长度至少3位';
      } else if (username.length > 10) {
        msg = '用户名长度最多10位';
      } else if (password.length < 6) {
        msg = '密码长度至少6位';
      } else if (password.length > 15) {
        msg = '密码长度最多15位';
      }else if (password.includes(' ')) {
        msg = '密码不能包含空格';
      }else if (username.includes(' ')) {
        msg = '用户名不能包含空格';
      }
      if (msg) {
       showDialog({
          message: msg,
        }).then(() => {
          this.clearInputs();
        });
        return;
      }

      if (this.mode === '1') {
        this.handleLogin();
      } else if (this.mode === '0') {
        console.log("Registering...");
        this.handleRegister();
      }
    },
    handleLogin() {
      const hashedPassword = MD5(this.password).toString();
      this.$http({
        url: "/auth/login",
        method: "post",
        data: {
          username: this.username,
          password: hashedPassword,
        },
      })
          .then((response) => {
            if (response.data.code !== 0) {
              showDialog({
                title: "登录失败",
                message: response.data.msg,
              }).then(() => {
                this.clearInputs();
              });
              return;
            }
            const token = response.data.data.token;
            localStorage.setItem("token", token);
            const redirect = this.$route.query.redirect || "/";
            this.$router.push(redirect);
          })
          .catch((error) => {
            console.error("登录失败:", error);
            showDialog({
              title: "登录失败",
              message: error.response.data.message,
            }).then(() => {
              this.clearInputs();
            });
          });
    },
    handleRegister() {
      const hashedPassword = MD5(this.password).toString();

      this.$http({
        url: "/auth/register",
        method: "post",
        data: {
          username: this.username,
          password: hashedPassword,
        },
      })
          .then((response) => {
            if (response.data.code !== 0) {
              showDialog({
                title: "注册失败",
                message: response.data.msg,
              }).then(() => {
                this.clearInputs();
              });
              return;
            }
            const token = response.data.data.token;
            localStorage.setItem("token", token);
            //this.$store.commit("setToken", token);
            const redirect = this.$route.query.redirect || "/";
            this.$router.push(redirect);
          })
          .catch((error) => {
            console.error("注册失败:", error);

          });
    },
    clearInputs() {
      this.username = "";
      this.password = "";
    },
    onForgotPassword() {
      // 用户点击忘记密码后的处理逻辑
      showDialog({
        title: "忘记密码",
        message: "0.重置密码不会丢失记账数据\n1. 请登录服务器，找到部署的后台文件夹\n2. 删除如下文件./Server/auth/secret.key\n3. 如未找到文件，请修改compose启动文件\n4. 无需重启服务器，刷新页面重新注册即可\n5. 请妥善保管好您的密码",
      });
      console.log("点击了忘记密码");
    },
  },
};
</script>

<style scoped>
.login-register-container {
  padding: 16px;
  background-color: #f7f8fa;
  min-height: 100vh; /* 使用视口高度，确保容器至少和视口一样高 */
  overflow: hidden; /* 禁止滚动（包括横向和纵向） */
  display: flex;
  flex-direction: column;
}

/* 整体距离左侧20px，距离上部50px */
.header-container {
  margin-left: 20px;
  margin-top: 50px;
}

/* 图片和标题在同一行，且标题垂直居中 */
.logo-title {
  display: flex;
  align-items: center;
}

/* 标题样式 */
.title {
  font-size: 24pt;
  color: #323233;
  /* 可以增加左右间距，根据需要调整 */
  margin-left: 10px;
}

/* p元素样式，去除默认 margin 并与图片左边框对齐 */
.subtitle {
  font-size: 15pt;
  color: #969799;
  margin: 0;
  /* 如果需要 p 元素与上面的行有间距，可增加 margin-top */
  margin-top: 8px;
}

.button-group {
  margin: 20px 20px 0 20px;
}

.forgot-password {

  margin-top: 10px;
}

.forgot-password a {
  color: #1989fa;
  text-decoration: none;
}
</style>
