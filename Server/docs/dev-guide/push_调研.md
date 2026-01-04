# 消息推送方案调研

本文档调研 EasyAccounts 定时记账提醒功能的消息推送方案。

---

## 1. 需求背景

### 1.1 功能需求

- **定时记账提醒**：用户设置定期账单（房租、水电费、会员续费等）
- **临近日期推送**：提前 N 天推送提醒消息到用户微信
- **用户自部署**：EasyAccounts 是开源项目，用户自行部署服务器

### 1.2 架构设计

```
用户的 EasyAccounts 服务器
        ↓ HTTP 请求（携带用户标识）
开发者的中心推送服务器
        ↓ 微信 API
用户的微信
```

---

## 2. 微信推送方案对比

### 2.1 方案概览

| 方案 | 能否主动推送 | 次数限制 | 用户操作 | 门槛 |
|------|-------------|----------|----------|------|
| **服务号模板消息** | ✅ | 10万/天 | 关注公众号 | 企业认证（300元/年） |
| **订阅通知（一次性）** | ✅ | 点几次发几条 | 每次都要点订阅 | 认证服务号 |
| **订阅通知（长期）** | ✅ | 无限制 | 订阅一次 | 仅政务/医疗开放 |
| **企业微信（内部）** | ✅ | 无限制 | 加入企业 | 用户体验差 |
| **企业微信（外部）** | ⚠️ | 4条/月 | 添加为客户 | 太少 |
| **微信客服** | ⚠️ | 48小时内 | 用户先发消息 | 被动，不能主动推 |
| **微信测试号** | ✅ | 无限制 | 扫码关注 | 限100人 |

### 2.2 服务号模板消息（推荐）

**优点：**
- 用户关注一次，可无限次推送
- 用户体验自然（关注公众号）
- 完全可控

**限制：**
- 必须是**认证服务号**（需营业执照 + 300元/年）
- 订阅号不支持
- 个人无法申请

**使用限制：**
- 每个账号最多 25 个模板
- 每天总调用量 10 万次（粉丝超 10W/100W/1000W 会提升）
- 内容必须是服务通知，不能是广告营销

**API 示例：**

```json
POST https://api.weixin.qq.com/cgi-bin/message/template/send

{
  "touser": "用户的openid",
  "template_id": "模板ID",
  "data": {
    "title": { "value": "记账提醒" },
    "content": { "value": "您的房租 2000 元将于明天到期" },
    "time": { "value": "2026-01-06" }
  }
}
```

### 2.3 订阅通知

**一次性订阅：**
- 用户每点击一次订阅按钮，开发者获得发送 1 条消息的权限
- 用户要收到 10 条提醒，需要点 10 次订阅
- 用户体验差，不适合定时提醒场景

**长期订阅：**
- 用户订阅一次，可长期多次推送
- **仅向政务民生、医疗等公共服务领域开放**
- 普通开发者无法申请

### 2.4 企业微信

**内部应用消息：**
- 需要用户"加入企业"
- 用户体验奇怪（为什么要加入别人的企业？）
- 不推荐

**外部联系人：**
- 同一企业每月仅可针对一个客户发送 4 条消息
- 次数太少，不适合定时提醒

**微信客服：**
- 需要用户先发消息，48 小时内可回复
- 被动模式，不能主动推送

---

## 3. 第三方推送平台

### 3.1 PushPlus（推送加）

**官网：** https://www.pushplus.plus/

**支持渠道：**
- 微信公众号
- 短信、语音
- 邮件
- 企业微信、钉钉、飞书
- Bark、Gotify
- 浏览器插件、桌面应用

**使用方式：**
1. 用户关注 PushPlus 公众号
2. 获取个人 token
3. 调用 API 推送

```bash
curl -X POST https://www.pushplus.plus/send \
  -d "token=用户token&title=记账提醒&content=房租明天到期"
```

**优点：**
- 无需自建推送服务
- 免费额度足够个人使用
- 支持多种推送渠道

**缺点：**
- 依赖第三方服务
- 用户需要关注 PushPlus 公众号（而非你的公众号）

### 3.2 其他平台

| 平台 | 特点 |
|------|------|
| [个推](https://www.getui.com/) | 专业 APP 推送，支持统一推送标准 |
| [极光推送](https://www.jiguang.cn/push/) | 全平台（Android/iOS/鸿蒙/Web） |
| [LeanCloud](https://www.leancloud.cn/notification/) | 对接国内厂商推送 |
| [Message Pusher](https://github.com/songquanpeng/message-pusher) | 开源自建，Go 单文件 |

---

## 4. 其他推送方式

### 4.1 邮件推送

**优点：**
- 无门槛，免费
- 用户只需填邮箱

**缺点：**
- 打开率低
- 可能进垃圾箱

### 4.2 Telegram Bot

**优点：**
- 无限制推送
- API 简单

**缺点：**
- 国内用户需要科学上网

### 4.3 钉钉/飞书机器人

**优点：**
- 企业用户常用
- 免费

**缺点：**
- 个人用户不常用钉钉/飞书

---

## 5. 推荐方案

### 5.1 有企业资质

**首选：服务号模板消息**

```
用户关注你的服务号
      ↓
获取 openid，绑定到 EasyAccounts
      ↓
临近记账日期，推送模板消息
```

**成本：** 300元/年认证费

### 5.2 无企业资质

**方案 A：借用 PushPlus**

```
用户关注 PushPlus 公众号，获取 token
      ↓
token 填入 EasyAccounts 设置
      ↓
临近记账日期，调用 PushPlus API
```

**方案 B：通用 Webhook**

让用户自己配置推送方式：

```yaml
# EasyAccounts 推送配置
push:
  enabled: true
  webhook_url: https://www.pushplus.plus/send
  method: POST
  body_template: |
    {
      "token": "{{user_token}}",
      "title": "{{title}}",
      "content": "{{content}}"
    }
```

**方案 C：邮件**

最简单的兜底方案，配置 SMTP 发邮件。

---

## 6. 实施建议

### 6.1 短期方案

1. 先实现 **Webhook 通用接口**
2. 提供 PushPlus 配置示例
3. 提供邮件推送作为兜底

### 6.2 长期方案

1. 注册企业，申请认证服务号
2. 搭建推送中心服务
3. 用户关注公众号，绑定 openid
4. 提供更好的用户体验

---

## 7. 参考链接

- [微信服务号模板消息文档](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Template_Message_Interface.html)
- [模板消息运营规范](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Template_Message_Operation_Specifications.html)
- [企业微信开发文档](https://developer.work.weixin.qq.com/document/path/90236)
- [PushPlus 官网](https://www.pushplus.plus/)
- [Message Pusher GitHub](https://github.com/songquanpeng/message-pusher)

---

*文档版本：v1.0*
*调研时间：2026-01-05*
