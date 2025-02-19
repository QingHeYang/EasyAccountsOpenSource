// src/axios.js
import axios from 'axios';
import router from './router'; // 确保正确引入你的 Vue Router 实例
import { showNotify} from 'vant'; // 引入 Vant 的通知组件

// 创建一个 Axios 实例
const request = axios.create({

    baseURL: window.config.apiBaseUrl, // 替换为你的 API 基础地址
    timeout: 5000, // 请求超时时间
});

request.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token'); // 假设 token 存储在 localStorage 中
        if (token) {
            config.headers['Authorization'] = `${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// 添加响应拦截器
request.interceptors.response.use(
    response => {
        if (response.data.code !== 0) {

            if (response.data.code === 401) {
                router.push({
                    path: '/auth', // 确保路径与路由配置一致
                    query: { redirect: router.currentRoute.fullPath,mode:1}
                });
                return response;
            }else if(response.data.code === 418) {
                router.push({
                    path: '/auth', // 确保路径与路由配置一致
                    query: {
                        redirect: router.currentRoute.fullPath,
                        mode:0,
                    }
                });
                return response;
            }else {
                showNotify({
                    type: 'warning',
                    message: `${response.data.code}\n${response.data.msg}`,
                    duration: 2000,
                });
            }
            if (typeof caches === 'function') {
                caches();
            }
        }
        return response;
    },
    error => {
        if (error.response) {
            let { status, statusText } = error.response;
            // 如果状态码是 401，执行跳转
            if (status === 401) {
                statusText = '登录过期，请登录';
                localStorage.removeItem('token');
                // 跳转到登录页面，并携带当前页面路径作为重定向参数
                router.replace({
                    path: '/auth', // 确保路径与路由配置一致
                    query: { redirect: router.currentRoute.fullPath,mode:1 }
                });
            }else if(status === 418) {
                // 清除存储的 token
                statusText = '未查询到账号，请注册';
                localStorage.removeItem('token');
                // 跳转到登录页面，并携带当前页面路径作为重定向参数
                router.push({
                    path: '/auth', // 确保路径与路由配置一致
                    query: {
                        redirect: router.currentRoute.fullPath,
                        mode:0,
                    }
                });
            }else if(status === 500) {
                statusText = '服务器错误';
            }else if(status === 404) {
                statusText = '未找到请求资源';
            }else {
                statusText = '未知错误';
            }
            showNotify({
                type: 'danger',
                message: `${statusText}`,
                duration: 2000,
            });
        } else {
            showNotify({
                type: 'danger',
                message: `请求错误: ${error.message}`,
                duration: 800,
            });
        }
        //return Promise.reject(error);
        return error;
    }
);

export default request;
