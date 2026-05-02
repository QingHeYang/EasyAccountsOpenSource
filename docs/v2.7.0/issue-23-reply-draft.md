# Issue #23 回复草稿（v2.7.0 收尾）

> 这份是给 https://github.com/QingHeYang/EasyAccounts/issues/23 的回复草稿。
> 主管审完后由项目所有者发到 GitHub，发完后这份草稿可以删除。

---

## 回复正文

各位好，v2.7.0 即将发版，我作为项目主管 Claude 重新核查了这个 issue 的根因，**之前我的诊断有偏差**，在这里更正一下。

### 撤回上一次的诊断

之前我说"`user_id` header 被外层 nginx 丢弃（下划线问题）"，让大家加 `underscores_in_headers on;`。这个**配置加了确实有用**（因为它顺便也保留了 Connection header 的转发），但**不是真正的根因**。

### 真实根因

**项目代码 + 项目内置 nginx 都没问题**。WebSocket 连不上的真实原因是：**你自己写的反代 nginx 缺了 WebSocket Upgrade 三件套**：

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

不写这三行，nginx 默认会把 `Connection: upgrade` 改成 `Connection: close`，WebSocket 永远握不上手。AI 端日志里看到的"缺少 user_id 请求头"是 WebSocket 升级失败后请求降级成普通 HTTP 后的连锁现象。

### 正确做法

@xqq27 的反代配置示例补全后应该是：

```nginx
server {
    listen 80;
    server_name xxxx;

    location / {
        proxy_pass http://127.0.0.1:10669;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # ⭐ WebSocket Upgrade 三件套（不写就连不上 AI）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # ⭐ 长连接超时（默认 60s 容易把 AI 思考过程掐断）
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        # ⭐ SSE / MCP 关键：禁用缓冲
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### v2.7.0 版本侧的处理

考虑到这是个**很常见的反代部署坑**（不只你们俩，相信还有很多潜水用户也踩过），项目侧不改代码，**v2.7.0 新增一份完整的反向代理部署指南**：

- 文件：[`docs/deployment-reverse-proxy.md`](https://github.com/QingHeYang/EasyAccounts/blob/main/docs/deployment-reverse-proxy.md)
- 包含：HTTP / HTTPS 完整 nginx 模板、Caddy / Apache 模板、5 类常见坑、自查 checklist、排查步骤

升级 v2.7.0 后按这份指南改你们的反代配置，AI 助手应该就能正常用了。

@valuex @xqq27 这个 issue 我就 close 了。如果按指南改完还有问题，欢迎再开新 issue 附上：
1. 你的反代配置（脱敏域名 / IP）
2. 浏览器 F12 Network 截图（WebSocket 那条）
3. `docker logs easy_accounts_ai` 最近 50 行

感谢 @xqq27 提供的 A/B 对照复现，让真相能被还原 🙏
