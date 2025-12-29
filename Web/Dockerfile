# 使用官方的Nginx镜像作为基础镜像
FROM nginx:latest

# 维护者信息
LABEL maintainer="Mecy@deep-blue.cloud"

# 将dist目录拷贝到Nginx的默认HTML目录
COPY ydjz_web/dist/ /usr/share/nginx/html/
COPY ydjz_web/dist/config.js /usr/share/nginx/html/config.js

# 将nginx配置文件拷贝到镜像中
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 创建一个空的resources目录
RUN mkdir -p /usr/share/nginx/html/resources

# 暴露80端口
EXPOSE 80

# 启动Nginx（不再需要环境变量替换）
CMD ["nginx", "-g", "daemon off;"]
