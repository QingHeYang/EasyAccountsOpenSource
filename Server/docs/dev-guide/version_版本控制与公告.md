# 版本控制与公告

本文档介绍 EasyAccounts 的版本管理机制和公告通知系统。

---

## 目录

1. [版本号规范](#版本号规范)
2. [版本配置](#版本配置)
3. [版本更新检查](#版本更新检查)
4. [公告通知系统](#公告通知系统)
5. [云端文件管理](#云端文件管理)
6. [接口说明](#接口说明)

---

## 版本号规范

### 版本号格式

| 格式 | 说明 | 示例 |
|------|------|------|
| `version.release` | 3位版本号 | `2.6.1` |
| `version.code` | 4位版本码 | `2610` |

### version.code 规则

```
2610 = 2.6.1 第 0 次发版（首发）
2611 = 2.6.1 第 1 次修复
2612 = 2.6.1 第 2 次修复
```

| 位置 | 含义 | 说明 |
|------|------|------|
| 第1位 | 大版本 | 重大架构变更 |
| 第2位 | 中版本 | 新功能 |
| 第3位 | 小版本 | 功能优化/小改进 |
| 第4位 | 修复版本 | Bug 修复，0=首发 |

### 各模块版本

| 配置项 | 说明 | 对应 Docker 镜像 |
|--------|------|------------------|
| `version.release` | 整体版本号 | - |
| `version.font_branch` | 前端版本 | `easyaccounts-web` |
| `version.backend_branch` | 后端版本 | `easyaccounts-server` |
| `version.mysql_branch` | 数据库版本 | - |
| `version.agent_branch` | AI Agent 版本 | `easyaccounts-ai` |
| `version.webhook_branch` | WebHook 版本 | `easyaccounts-webhook` |

---

## 版本配置

### 配置文件

**application-server.properties:**
```properties
# 版本信息
version.release=2.6.1
version.code=2610
version.font_branch=4.0.1
version.backend_branch=2.6.1
version.mysql_branch=2.5.0
version.agent_branch=1.1.0
version.webhook_branch=1.0.0

# 云端版本通知 JSON 地址
version.notice.url=https://blue-out-share.oss-cn-zhangjiakou.aliyuncs.com/version-notice.json

# 公告通知 JSON 地址
notices.url=https://blue-out-share.oss-cn-zhangjiakou.aliyuncs.com/notices.json
```

### 本地开发

本地开发版本添加 `-local` 后缀：

```properties
version.release=2.6.1-local
version.font_branch=4.0.1-local
```

---

## 版本更新检查

### 机制

应用启动时自动检查云端版本，通过比较 `versionCode` 判断是否有更新。

### 云端 version-notice.json

```json
{
  "version": "2.6.1",
  "versionCode": 2610,
  "releaseDate": "2026-01-26",
  "changelog": "## v2.6.1 更新内容\n\n### 新增功能\n- 数据库备份恢复接口\n- 恢复后自动重启\n\n### 优化\n- 跨平台支持",
  "modules": {
    "web": "4.0.1",
    "server": "2.6.1",
    "ai": "1.1.0",
    "webhook": "1.0.0",
    "mysql": "2.5.0"
  }
}
```

### 检查逻辑

```java
// VersionUtils.java
private VersionDto.Update checkUpdate() {
    // 1. 获取云端 JSON
    // 2. 比较 versionCode
    if (localVersionCode < remoteVersionCode) {
        // 3. 返回更新信息
        return update;
    }
    return null;
}
```

### 响应结构

```json
{
  "versions": {
    "release": "2.6.1",
    "versionCode": 2610,
    "fontBranch": "4.0.1",
    "backendBranch": "2.6.1"
  },
  "update": {
    "version": "2.6.2",
    "versionCode": 2620,
    "releaseDate": "2026-02-01",
    "changelog": "..."
  }
}
```

如果没有更新，`update` 字段为 `null`。

---

## 公告通知系统

### 概述

独立于版本更新的公告系统，用于向用户推送通知消息。**用户主动调用**获取公告列表。

### 云端 notices.json

```json
{
  "notices": [
    {
      "id": 1,
      "title": "v2.6.1 发布",
      "content": "新增数据库备份恢复功能，支持任意版本备份恢复",
      "date": "2026-01-26",
      "url": "",
      "expire": "2026-02-28"
    },
    {
      "id": 2,
      "title": "欢迎反馈",
      "content": "使用中遇到问题欢迎在 GitHub 提交 Issue",
      "date": "2026-01-26",
      "url": "https://github.com/QingHeYang/EasyAccounts/issues",
      "expire": ""
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 是 | 公告唯一标识，前端记录已读状态 |
| `title` | string | 是 | 公告标题 |
| `content` | string | 是 | 公告内容 |
| `date` | string | 是 | 发布日期 (yyyy-MM-dd) |
| `url` | string | 否 | 跳转链接，空则无链接 |
| `expire` | string | 否 | 过期日期，空则永不过期 |

### 服务端处理

**NoticeService.java:**
```java
public List<NoticeDto.Notice> getNotices() {
    // 1. 获取云端 JSON
    // 2. 解析公告列表
    // 3. 过滤已过期公告
    return notices.stream()
            .filter(notice -> !isExpired(notice, today))
            .collect(Collectors.toList());
}

private boolean isExpired(NoticeDto.Notice notice, LocalDate today) {
    if (notice.getExpire() == null || notice.getExpire().isEmpty()) {
        return false;  // 永不过期
    }
    LocalDate expireDate = LocalDate.parse(notice.getExpire());
    return today.isAfter(expireDate);
}
```

### 前端处理建议

```javascript
// 1. 获取公告列表
const notices = await fetch('/api/home/getNotices').then(r => r.json());

// 2. 获取本地已读列表
const readIds = JSON.parse(localStorage.getItem('readNoticeIds') || '[]');

// 3. 过滤未读公告
const unreadNotices = notices.data.filter(n => !readIds.includes(n.id));

// 4. 显示未读公告（小红点、弹窗等）
if (unreadNotices.length > 0) {
    showNoticeBadge(unreadNotices.length);
}

// 5. 标记已读
function markAsRead(noticeId) {
    readIds.push(noticeId);
    localStorage.setItem('readNoticeIds', JSON.stringify(readIds));
}
```

---

## 云端文件管理

### 文件列表

| 文件 | 地址 | 用途 |
|------|------|------|
| version-notice.json | `https://blue-out-share.oss-cn-zhangjiakou.aliyuncs.com/version-notice.json` | 版本更新检查 |
| notices.json | `https://blue-out-share.oss-cn-zhangjiakou.aliyuncs.com/notices.json` | 公告通知 |

### 更新流程

1. 修改本地 JSON 文件（`docs/` 目录）
2. 上传到阿里云 OSS
3. 用户下次请求获取最新内容

### 本地模板

```
docs/
├── notices.json           # 公告模板
└── version-notice.json    # 版本通知模板（可选）
```

---

## 接口说明

### 获取版本信息

**接口：** `GET /home/getVersion`

**说明：** 获取当前版本信息，自动检查是否有更新

**响应：**
```json
{
  "code": 0,
  "msg": "Success",
  "data": {
    "versions": {
      "release": "2.6.1",
      "versionCode": 2610,
      "fontBranch": "4.0.1",
      "backendBranch": "2.6.1",
      "mysqlBranch": "2.5.0",
      "agentBranch": "1.1.0",
      "webhookBranch": "1.0.0"
    },
    "auth": {
      "enable": false,
      "expiredMinutes": 30,
      "singleLogin": true
    },
    "backup": {
      "cron": "0 0 22 * * ?",
      "valid": true,
      "description": "已配置自动备份"
    },
    "update": null
  }
}
```

### 获取公告列表

**接口：** `GET /home/getNotices`

**说明：** 用户主动调用获取公告列表，自动过滤已过期公告

**响应：**
```json
{
  "code": 0,
  "msg": "Success",
  "data": [
    {
      "id": 1,
      "title": "v2.6.1 发布",
      "content": "新增数据库备份恢复功能",
      "date": "2026-01-26",
      "url": "",
      "expire": "2026-02-28"
    }
  ]
}
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `dto/VersionDto.java` | 版本信息数据结构 |
| `dto/NoticeDto.java` | 公告数据结构 |
| `utils/VersionUtils.java` | 版本检查工具类 |
| `service/NoticeService.java` | 公告服务 |
| `controller/HomeController.java` | 版本和公告接口 |
| `docs/notices.json` | 公告模板 |
