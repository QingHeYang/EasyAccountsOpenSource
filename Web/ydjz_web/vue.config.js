module.exports = {
  devServer: {
    host: '0.0.0.0',
    port: 8081,
    // open: true, //配置自动启动浏览器
    historyApiFallback: true, // 支持HTML5 history模式路由
    proxy:{
      "/ai-api":{
        changeOrigin: true,
        ws: false,
        target: "http://192.168.50.226:8001",
        pathRewrite: {
          "^/ai-api": ""
        },
        logLevel: 'debug',
        onProxyReq: function(proxyReq, req, res) {
          console.log('Proxying:', req.method, req.url, '-> http://192.168.50.226:8001' + req.url.replace('/ai-api', ''));
        }
      },
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
  // 确保config.js等静态资源能正确访问
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/'
};