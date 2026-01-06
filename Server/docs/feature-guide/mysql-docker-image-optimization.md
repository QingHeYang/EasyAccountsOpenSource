# MySQL Docker 镜像优化方案

## 背景

当前部署流程需要用户手动复制数据库初始化文件：

```bash
cp Database/base_sql/yd_jz_base.sql Database/init/yd_jz_base.sql
```

存在问题：
1. 步骤繁琐，容易遗忘
2. 某些系统有权限问题
3. 用户体验不佳

## 优化方案

将 `base_sql` 打包进自定义 MySQL 镜像，简化部署流程。

### 镜像结构

```dockerfile
# Database/Dockerfile
FROM mysql:8.0.31
COPY base_sql/yd_jz_base.sql /docker-entrypoint-initdb.d/
```

### docker-compose.yml 修改

```yaml
services:
  db:
    # 原来
    # image: mysql:8.0.31

    # 改为
    build: ./Database

    volumes:
      - ./Database/data:/var/lib/mysql
      # 如需恢复数据，取消下行注释，将备份SQL放入init目录，删除data目录后重启
      # - ./Database/init:/docker-entrypoint-initdb.d
```

### 目录结构

```
Database/
├── Dockerfile          # 新增
├── base_sql/
│   └── yd_jz_base.sql  # 基础数据（打进镜像）
├── init/
│   └── .gitkeep        # 恢复备份用（空目录）
└── data/               # MySQL 数据目录（gitignore）
```

---

## 使用场景

### 场景 1：首次部署

```bash
git clone https://github.com/QingHeYang/EasyAccounts.git
cd EasyAccounts
docker-compose up -d
```

直接启动，镜像内的 `base_sql` 自动初始化数据库。

### 场景 2：恢复备份数据

1. 将备份 SQL 放入 `Database/init/` 目录
2. 修改 `docker-compose.yml`，取消 init 映射的注释：
   ```yaml
   - ./Database/init:/docker-entrypoint-initdb.d
   ```
3. 删除数据目录：
   ```bash
   rm -rf Database/data/*
   ```
4. 重启容器：
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### 场景 3：完全重置

```bash
rm -rf Database/data/*
docker-compose down
docker-compose up -d
```

数据目录清空后重启，自动用镜像内 base_sql 初始化。

---

## 原理说明

### MySQL 初始化机制

MySQL 官方镜像在**首次启动**（数据目录为空时）会自动执行 `/docker-entrypoint-initdb.d/` 目录下的 `.sql` 文件。

### Volume 覆盖机制

当 volume 映射到 `/docker-entrypoint-initdb.d/` 时，会覆盖镜像内的文件：

| compose 配置 | 效果 |
|-------------|------|
| 注释掉 init 映射 | 使用镜像内 base_sql |
| 取消注释 | 使用外部 init 目录的文件 |

---

## 镜像管理

### 构建镜像

```bash
cd Database
docker build -t easyaccounts-mysql:2.6.0 .
```

### 推送镜像

```bash
# Docker Hub
docker push yourusername/easyaccounts-mysql:2.6.0

# 阿里云
docker push registry.cn-hangzhou.aliyuncs.com/xxx/easyaccounts-mysql:2.6.0
```

### 更新频率

- `base_sql` 基本不变，有 Liquibase 处理后续迁移
- 仅在表结构大改时需要重新构建镜像

---

## 版本管理

在 `application-server.properties` 中添加：

```properties
version.mysql_branch=2.6.0
```

---

## 文件变更清单

| 操作 | 文件 |
|------|------|
| 新增 | `Database/Dockerfile` |
| 新增 | `Database/init/.gitkeep` |
| 修改 | `docker-compose.yml` |
| 修改 | `docker-compose-chinese.yml` |
| 修改 | 部署文档 |
