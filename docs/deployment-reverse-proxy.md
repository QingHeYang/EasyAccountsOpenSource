# 反向代理部署指南

> 适用场景：你想用 nginx / Caddy / Apache 等反向代理把 EasyAccounts 挂到 80/443 端口、绑定域名或加 HTTPS。
> v2.7.0 起，用户报"AI 助手连不上"99% 是反代配置问题（issue #23 系列）。本文给出完整模板 + 常见坑。

---

## 一、部署架构

```
浏览器
   ↓
用户的反向代理（你自己写的 nginx，监听 80/443）
   ↓ proxy_pass
EasyAccounts 容器入口（默认 10669 端口）= 项目内置 nginx
   ↓ 内部网桥
   ├── server  容器（后端 API）
   └── ai      容器（WebSocket / SSE / MCP）
```

**核心要点**：你的反代不只要转发 HTTP，**还要转发 WebSocket 升级请求**。这是 99% 用户连不上 AI 的根因。

---

## 二、完整 nginx 配置模板（HTTP）

```nginx
server {
    listen 80;
    server_name your-domain.com;     # 改成你的域名

    # —— 基础代理 ——
    location / {
        proxy_pass http://127.0.0.1:10669;     # 改成你的 EasyAccounts 容器映射端口

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # ⭐⭐⭐ 关键三件套（不写就连不上 AI）⭐⭐⭐
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # —— 长连接超时 ——
        # WebSocket / SSE / MCP 都是长连接，默认 60s 容易被掐断
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        # —— SSE / MCP 关键：禁用缓冲 ——
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## 三、HTTPS 模板

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /path/to/your/fullchain.pem;
    ssl_certificate_key /path/to/your/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:10669;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket Upgrade（同上）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
        proxy_cache off;
    }
}

# 强制 HTTP → HTTPS 跳转（可选）
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

> **HTTPS 后浏览器自动用 `wss://`**：前端会读 `window.location.protocol`，是 `https:` 就连 `wss://`，是 `http:` 就连 `ws://`，自动适配，无需手动改。

---

## 四、常见坑 ⚠️

### 坑 1：缺 WebSocket Upgrade 三件套（最常见）

**症状**：前端登录正常，记账正常，但 AI 助手"连接失败"。

**根因**：`Upgrade` / `Connection` header 没转发，nginx 默认会把 `Connection: upgrade` 改成 `Connection: close`，WebSocket 永远握不上手。

**修复**：上面模板里那 3 行必须有：
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 坑 2：长连接 60 秒后被掐断

**症状**：AI 助手能连上，但聊到一半突然"连接断开"。

**根因**：nginx 默认 `proxy_read_timeout 60s`，AI 思考超过 60 秒被掐。

**修复**：
```nginx
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

### 坑 3：SSE / MCP 流式响应卡顿

**症状**：用 Cherry Studio / Claude Desktop 等客户端连 MCP 时，响应一卡一卡。

**根因**：nginx 默认开启响应缓冲。

**修复**：
```nginx
proxy_buffering off;
proxy_cache off;
```

### 坑 4：WSS（HTTPS）下 Mixed Content

**症状**：用 HTTPS 域名访问，浏览器控制台报 "Mixed Content: ws:// blocked"。

**根因**：前端从 `https://` 页面打开 `ws://` WebSocket，被浏览器安全策略阻断。

**修复**：检查反代是否正确转发了 `X-Forwarded-Proto $scheme;`，前端会根据这个判断用 `wss://`。如果用了 Cloudflare 等多层代理，要确保整条链路都是 HTTPS。

### 坑 5：CDN / 多层代理脱壳问题

**症状**：套了 Cloudflare 等 CDN，AI 助手随机性连不上。

**根因**：免费版 Cloudflare 对 WebSocket 支持有限制；或多层代理只有最外层透传了 Upgrade，中间一层没透传。

**修复**：
- 关闭 Cloudflare 的 "Proxy"（橙色云朵）改为 "DNS only"（灰色云朵）
- 或升级到 Cloudflare 付费版以获得更好的 WebSocket 支持
- 排查每一层代理的配置

---

## 五、自查 checklist

部署完用浏览器访问反代域名，**所有项都过**才算配置成功：

- [ ] `http(s)://你的域名/` → 能正常打开 EasyAccounts 登录页
- [ ] 登录后能正常看到流水 / 账户
- [ ] 点击 AI 助手按钮 → 抽屉打开，能输入消息
- [ ] 输入消息后能看到 AI 流式回复（不是 "连接失败"）
- [ ] AI 调工具（如查账户）能正常返回结果
- [ ] AI 思考超过 60 秒不会被掐断

---

## 六、还是连不上？排查步骤

### 步骤 1 · 直连内网验证

**先绕开你的反代**，直接访问 EasyAccounts 容器映射端口（如 `http://你的IP:10669/`），如果 AI 助手在直连模式下能用：

→ 100% 是你反代的问题，不是项目的问题。回到第四节看坑 1-3。

### 步骤 2 · 看浏览器开发工具

打开浏览器 F12 → Network → 筛选 WS：

| 现象 | 含义 |
|---|---|
| `/ws/chat` 状态 `101 Switching Protocols` | ✅ WebSocket 握手成功 |
| `/ws/chat` 状态 `400 / 502 / 504` | ❌ 反代没转发 Upgrade，看坑 1 |
| `/ws/chat` 状态 `200`（响应不是 101） | ❌ 同上 |
| `/ws/chat` 红色 `(failed)` | ❌ 看 console 报错信息 |

### 步骤 3 · 看 nginx error log

```bash
tail -f /var/log/nginx/error.log
```

报 `upstream prematurely closed connection` 通常是后端容器没起；
报 `Connection refused` 通常是 `proxy_pass` 写错。

### 步骤 4 · 看 EasyAccounts 容器日志

```bash
docker logs -f easy_accounts_ai
```

如果一直没看到 `WebSocket连接已建立` 字样，说明 WebSocket 升级请求**没到 ai 容器**，问题在反代或内部 nginx 之前。

---

## 七、其他反代软件参考

### Caddy

```caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:10669 {
        # Caddy 默认就支持 WebSocket，无需额外配置 Upgrade
        transport http {
            read_timeout 1h
            write_timeout 1h
        }
    }
}
```

### Apache (httpd)

需启用 `mod_proxy`、`mod_proxy_http`、`mod_proxy_wstunnel`：

```apache
<VirtualHost *:80>
    ServerName your-domain.com

    ProxyPreserveHost On
    ProxyPass /ws/ ws://127.0.0.1:10669/ws/
    ProxyPassReverse /ws/ ws://127.0.0.1:10669/ws/
    ProxyPass / http://127.0.0.1:10669/
    ProxyPassReverse / http://127.0.0.1:10669/

    ProxyTimeout 3600
</VirtualHost>
```

---

## 八、更多帮助

- 项目 issue：https://github.com/QingHeYang/EasyAccounts/issues
- 历史相关 issue：[#23](https://github.com/QingHeYang/EasyAccounts/issues/23)
- 提交问题前请附带：
  - 你的反代配置（脱敏域名 / IP）
  - 浏览器 F12 Network 截图（WebSocket 那条）
  - `docker logs easy_accounts_ai` 最近 50 行
