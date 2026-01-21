# EasyAccounts MySQL 镜像
# 基于官方 MySQL 8.0.31，内置初始化脚本

FROM mysql:8.0.31

LABEL maintainer="Mecy@deep-blue.cloud"
LABEL description="EasyAccounts MySQL with built-in initialization script"

# 复制初始化 SQL 到 docker-entrypoint-initdb.d
# MySQL 会在首次启动时自动执行该目录下的 SQL 文件
COPY yd_jz_base.sql /docker-entrypoint-initdb.d/

# 复制内存优化配置
COPY my.cnf /etc/mysql/conf.d/optimize.cnf

# 设置字符集
ENV MYSQL_DATABASE=yd_jz
ENV LANG=C.UTF-8
