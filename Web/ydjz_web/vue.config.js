module.exports = {
  devServer: {
    host: '0.0.0.0',
    port: 8081,
    // open: true, //配置自动启动浏览器
    proxy:{
      "/api":{
        changeOrigin:true,
        ws:false,
        target: "http://yd_service:8081/",
        pathRewrite:{
          "^/api":""
        }
      }
    }
  },

};