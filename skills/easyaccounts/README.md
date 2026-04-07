# EasyAccounts Skill for OpenClaw

让你的 OpenClaw AI 助手成为家庭财务管家 — 通过自然语言记账、查账、统计和导出报表。

> 对接 [EasyAccounts](https://github.com/QingHeYang/EasyAccounts) 个人记账系统。

---

## 它能做什么

- **🦞 记一笔流水** — "记一下午餐 30 块"
- **🦞 批量记账** — "今天的:午餐 30、地铁 12、咖啡 25"
- **🦞 查询流水** — "查上个月的餐饮支出"、"今年最大的 5 笔开销"
- **🦞 修改流水** — "把刚才那笔午餐改成 35"
- **🦞 内部转账** — "从微信转 500 到银行卡"
- **🦞 年度统计** — "今年总收入多少"、"现在总资产多少"
- **🦞 导出 Excel** — "把 3 月的账单导出"
- **🦞 系统信息** — "有什么新公告"、"我用的什么版本"

所有由本 skill 创建的流水会标记 `from=Claw` 和备注末尾追加 `#Claw记账`,方便你区分。

---

## 安装

```bash
clawhub install easyaccounts
# 或
openclaw skills install easyaccounts
```

## 配置

在 `~/.openclaw/.env` 中设置:

```bash
# 必需
EASYACCOUNTS_URL=http://your-easyaccounts-server:8081
# 或带 nginx 代理路径
# EASYACCOUNTS_URL=http://example.com/api

# 可选(仅服务端开启了登录时需要)
EASYACCOUNTS_USERNAME=admin
EASYACCOUNTS_PASSWORD=yourpassword
```

> 安全建议:`chmod 600 ~/.openclaw/.env`

## 依赖

- `curl`(几乎所有系统都自带)
- `jq` — JSON 处理
  - macOS: `brew install jq`
  - Ubuntu/Debian/WSL: `apt install jq`
  - Windows: 走 WSL2,或下载 [jq for Windows](https://jqlang.github.io/jq/download/)

OpenClaw 在 Windows 推荐使用 WSL2,本 skill 在 WSL2 内运行无任何额外配置。

---

## 使用示例

配置好后,直接对你的 OpenClaw 代理说话即可:

> **你**:今天午餐花了 35,记一下
> **AI**:已记录,流水 ID #4828:现金 -35.00,分类:餐饮,日期:2026-04-07

> **你**:查一下这个月吃饭花了多少
> **AI**:本月餐饮支出共 8 笔,合计 ¥523.50,占总支出 31%。最大一笔是…

> **你**:今天的:午餐 30、地铁 12、咖啡 25,记一下
> **AI**:已批量记 3 笔,总计 ¥67.00 …

---

## 不支持的操作

出于**安全考虑**,本 skill **不提供以下功能**:

- ❌ 删除流水(需到 EasyAccounts 前端手动删除)
- ❌ 删除/创建账户、分类、动作(主数据维护请用前端)

---

## 配套前端识别

本 skill 写入的流水带 `from=Claw` 标记。如果你的 EasyAccounts 前端是 v2.6.1+,会显示一个**粉色 `Claw` 标签**;旧版本只显示备注里的 `#Claw记账` 文字。

---

## 项目地址

- **本 Skill**:[GitHub](https://github.com/QingHeYang/EasyAccounts/tree/main/skills/easyaccounts)
- **EasyAccounts 主项目**:[GitHub](https://github.com/QingHeYang/EasyAccounts)
- **问题反馈**:[Issues](https://github.com/QingHeYang/EasyAccounts/issues)

## License

MIT-0(MIT No Attribution),允许任何使用包括商用,无附加条款。
