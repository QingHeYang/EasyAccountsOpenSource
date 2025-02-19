# 使用 Ubuntu 作为基础镜像
FROM ubuntu:latest

# 维护者信息
LABEL maintainer="Mecy@deep-blue.cloud"

# 暴露端口 8081
EXPOSE 8081

# 设置环境变量
ENV LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# 安装必要的软件和 OpenJDK 11
RUN apt-get update \
    && apt-get install -y vim tree net-tools mysql-client \
    && apt-get install -y openjdk-11-jdk

# 设置 JAVA_HOME 环境变量
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# 创建必要的目录并设置权限
RUN mkdir -p /Ledger/config/ /Ledger/excel/month/ /Ledger/excel/screen/ /Ledger/excel/analysis/ /Ledger/excel_template/ /Ledger/backup/ /Ledger/app/ /Ledger/logs/ \
    && chmod -R 777 /Ledger

# 复制 excel_template 目录下的 xls 文件到容器内的 /Ledger/excel_template/ 目录
COPY excel_template/*.xls /Ledger/excel_template/

# 复制编译好的 JAR 文件到容器内的 /Ledger/app/ 目录
COPY YD_JZ/target/YD_JZ-SNAPSHOT.jar /Ledger/app/

# 设置工作目录
WORKDIR /Ledger

# 设置容器启动时执行的命令
CMD ["java", "-jar", "/Ledger/app/YD_JZ-SNAPSHOT.jar", "-Duser.timezone=GMT+8"]
