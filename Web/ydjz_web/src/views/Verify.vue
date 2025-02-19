<template>
  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; box-sizing: border-box;">
    <div class="qr-code" v-if="bindData" style="width: 100%; max-width: 360px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; border-radius: 10px;">
      <h1 style="margin-bottom: 20px;">绑定验证码</h1>
      <img :src="'data:image/png;base64,' + bindData.qrcode" style="max-width: 100%; height: auto; margin-bottom: 20px;"/>

      <div style="display: flex; align-items: center; margin-top: 10px;">
        <input style="flex-grow: 1; padding: 10px; margin-right: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 12px;" type="text" v-model="bindData.secret" readonly>
      </div>
    </div>

    <div style="width: 100%; max-width: 360px; margin-top: 20px;">
      <input type="password" placeholder="请输入密码" v-model="password" style="width: 100%; padding: 12px 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px;"/>
    </div>

    <div style="width: 100%; max-width: 360px; margin-top: 20px;">
      <van-button type="success" block size="large">验证</van-button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      bindData: {
        qrcode: 'iVBORw0KGgoAAAANSUhEUgAAAcIAAAHCAQAAAABUY/ToAAACmElEQVR4nO2aQW7rMAxEBfgAPpKv7iPlAAH4bYpD0Zbb/nbZPi2URNTTakBSozT74dgbJCQkJCQkJOQvIluMxdrWl5djWs9ATttLuzZIyJn0H/by/e82piOgnx4dmyEhb+Qpre2IHUp7S1+r6SCXpUeLQCEhH8ljuNyspzHfCgn5LTKS17nqBx0BfYOE/Iw0u8aONNb7J8vpi/oJ+cfJ0o2/Ppy+6uMh/zJZxq7bm5lLsFdB7S/7ICErGenp3O+GQMSi9mnEte5ePyEhtSwDacmK51tb+gN2ue9BQlbSV6rwSkvearO1T904JGSQrV102CKhRT3sqe2W3yAhK7kJd6h/urltmuLwuX5CQnb1KWWNRGWmB5I4Y1RGSMiJjF1KTyqKrUwdn6ogJKQymFc8Uz0s6hs/3btc77qFhAy5pdKya+prJo+pC6+tZpCQD2Tc3nzoaa3Uvl4K07HcICEfyCI8Zau8zKkvt3yHg4ScyVXuZFvjoOF665FtefI1ISGlvqXc48Lm7qG0BnouMxMBCXklm1yBTFkuQZdbjDwXEnIie7baLxukQz8y7CW1U5CQz2RIK7umURTzf2zzay0kpMVQnRuTP9naK9KX+nINSMgrWR9D8lpn7/otbnmPNzpIyMhWowpe7KXIW+rGISEfyGIgxf+Nxt2uqaeyEYCEvJPSlyreng9qHs3A6LMgIa/k0y5L9ckp+KAbh4S0WgCLw93lJhsgmqjJFYCEjGX/kL2kzvtEs8UK9ZlBQj6SPVEtVXijLy9itHsGg4S8k11aq8mxzCYqzUpIyE/JmrfWdytn1Hc4SMiZ9I+XfO09raS0AZTf7q4AJGRfjjHs69xvmbdObU7/XoOEvLsC/z0gISEhISEhIX8J+Q/AetwQIxAc+AAAAABJRU5ErkJggg==',
        secret: '4BXTTR4XJ5A2UOA3P4I7XFXOKQ5LC2HY',
      },
      password: '',
    };
  },
  methods: {
    handleInput(index) {
      this.digits[index] = this.digits[index].slice(-1).replace(/[^0-9]/g, '');  // Ensure the last character is numeric
      // Auto-focus next input field
      if (this.digits[index] && index < 5) {
        this.$refs[`pinInput${index + 1}`][0].focus();
      }
    },
    copyKey() {
      const input = this.$refs.secretKeyInput;
      input.select();
      document.execCommand('copy');
    },
    verifyCode() {
      const fullCode = this.digits.join('');
      console.log("Verifying code:", fullCode);
      // Integration with verification logic here
    }
  }
}
</script>

<style scoped>


.qr-code img {
  width: 100%;
  max-width: 300px;
  margin: 20px 0;
}


.pin-input {
  width: 40px;
  padding: 10px;
  font-size: 16px;
  text-align: center;
  border-radius: 5px;
  border: 1px solid #ccc;
}

.verify-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  border-radius: 5px;
  cursor: pointer;
}

.secret-key-container {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.secret-key-input {flex-grow: 1;padding: 10px;margin-right: 10px;border: 1px solid #ccc;border-radius: 5px;font-size: 12px;}

.copy-button {
  padding: 10px 20px;
  background-color: #007BFF;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

</style>
