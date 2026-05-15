# Eclipse Temurin 官方 OpenJDK 17 JRE（基于 Ubuntu 22.04 jammy）
# v2.8.0 起从 ubuntu:latest+完整 JDK 切到 JRE 镜像，体积 1.13GB → ~350MB
FROM eclipse-temurin:17-jre-jammy

LABEL maintainer="Mecy@deep-blue.cloud"

EXPOSE 8081

ENV LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# 安装 mysql-client（用于 SQLBackUpTask 调 mysqldump）
RUN apt-get update \
    && apt-get install -y --no-install-recommends mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建必要的目录并设置权限
RUN mkdir -p /Ledger/config/ /Ledger/excel/month/ /Ledger/excel/screen/ /Ledger/excel/analysis/ /Ledger/excel_template/ /Ledger/backup/ /Ledger/app/ /Ledger/logs/ \
    && chmod -R 777 /Ledger

# 复制 excel_template 目录下的 xlsx 文件到容器内的 /Ledger/excel_template/ 目录
COPY YD_JZ/excel_template/*.xlsx /Ledger/excel_template/

# 复制编译好的 JAR 文件到容器内的 /Ledger/app/ 目录
COPY YD_JZ/target/YD_JZ-SNAPSHOT.jar /Ledger/app/

WORKDIR /Ledger

# 设置容器启动时执行的命令（内存优化版，约200MB）
CMD ["java", "-Duser.timezone=Asia/Shanghai", \
     "-XX:MaxRAM=200m", \
     "-Xss512k", \
     "-XX:+UseSerialGC", \
     "-jar", "/Ledger/app/YD_JZ-SNAPSHOT.jar"]
