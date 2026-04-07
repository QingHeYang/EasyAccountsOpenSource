---
name: easyaccounts
description: 家庭财务管家。管理 EasyAccounts 个人记账系统的账户、分类、流水,支持收支记录、查询、统计和 Excel 报表导出。
homepage: https://github.com/EasyAccounts
metadata:
  openclaw:
    requires:
      bins: [curl, jq]
      env: [EASYACCOUNTS_URL]
    primaryEnv: EASYACCOUNTS_URL
    install:
      - id: brew
        kind: brew
        formula: jq
        bins: [jq]
        label: 安装 jq (brew)
      - id: apt
        kind: apt
        package: jq
        bins: [jq]
        label: 安装 jq (apt)
---

# EasyAccounts 家庭财务管家

你是一个家庭小财务官,负责管理 EasyAccounts 个人记账系统。本 skill 提供完整的记账能力:查询账户、记录收支、生成报表。

## 何时使用

- 用户要求**记账、查账、统计收支**(如"记一笔午餐 30 块"、"查上个月支出"、"导出 1 月账单")
- 用户提到**账户余额、分类消费、年度总结**
- 涉及 EasyAccounts 系统的任何操作

## 何时不使用

- 用户只是闲聊财务话题,没有具体操作请求
- 涉及股票、基金、加密货币等投资类查询(本系统不支持)

---

## 准备工作

### 1. 环境变量

- `EASYACCOUNTS_URL` (必需):EasyAccounts 后端服务地址,如 `http://localhost:8081`

### 2. 登录

首次使用前必须登录。token 会保存到 `~/.config/easyaccounts/token`,后续所有操作自动读取。

```bash
bash {baseDir}/scripts/login.sh <username> <password>
```

如果遇到 401 错误,提示用户重新登录即可。

---

## ⚠️ 核心业务规则(极其重要)

### typeId 和 actionId 的区别(不可混淆)

这是本系统最容易出错的地方,请务必理解:

- **typeId**:记账分类(科目),如"餐饮"、"交通"。从 `types` 接口的 `id` 字段获取。
- **actionId**:收支动作(借/贷),决定这笔账是收入还是支出。获取方式有两种:
  1. 分类已绑定 action → `types` 返回数据中 `actionId` 字段不为 null,直接用
  2. 分类未绑定 action → `actionId` 为 null,**必须**调用 `actions` 接口获取

**typeId 是"花在什么上",actionId 是"收还是支",两者完全不同!**

### 收支类型(handle)取值

- `0` = 收入
- `1` = 支出
- `2` = 内部转账
- `3` = 全部(仅查询时使用)

`handle` 不是 `actionId`,只是收支方向标识。

### 分类可用性规则

每个分类标注"可用"或"不可用":
- 有子分类的一级分类 → **不可用**(必须选其子分类)
- 无子分类的一级分类 → 可用
- 所有二级分类 → 可用

只能使用标注为"可用"的分类。

### 金额规则

- **只传正数**,不要带负号
- 系统根据 actionId 的收支类型自动处理正负
- 格式如 `"100.00"`,保留 2 位小数

---

## ⚠️ JSON 字段名注意事项(易踩坑)

后端使用 Lombok + Jackson,某些字段会被特殊序列化(首字母小写但第二个字母大写的字段会被全小写化)。**不同接口的字段名不一致**,请严格按下表使用:

### accounts 接口返回字段(`/account/getAccount`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 账户 ID |
| `name` | string | 账户名(注意:**不是** `aname`) |
| `money` | string | 余额 |
| `exemptMoney` | string | 免计金额 |
| `accountType` | int | 0=资产,1=负债 |
| `note` | string | 备注 |
| `card` | string | 卡号 |

### flows 接口返回字段(`/screen/getFlowByScreen`、`/flow/getFlow`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 流水 ID |
| `aname` | string | 账户名(**注意小写,不是 `aName` 也不是 `name`**) |
| `tname` | string | 分类名(同上) |
| `hname` | string | 收支动作名(如"支出"、"收入") |
| `handle` | int | 收支类型 0/1/2 |
| `money` | string | 金额 |
| `fdate` | string | 流水日期(**注意小写,不是 `fDate`**) |
| `note` | string | 备注 |
| `toAName` | string | 转入账户名(**注意这个反而是驼峰**,内部转账时有值) |
| `from` | string | 来源标记 |
| `collect` | bool | 是否收藏 |
| `hasImages` | bool | 是否有图片 |

### types 接口返回字段(`/type/getType`)

| 字段 | 说明 |
|------|------|
| `id` | 分类 ID(**这就是 typeId**) |
| `tname` | 分类名(注意小写) |
| `action.id` | actionId(可能为 null) |
| `action.handle` | 收支方向 |
| `action.hname` | 动作名 |
| `childrenTypes` | 子分类列表(有则一级分类不可用) |

### 一句话记忆

> **accounts 用 `name`,flows/types 用 `aname`/`tname`**(因 Lombok 序列化差异)。

---

## 工具调用流程

### 流程 A:查询流水

```
1. 调用 current_date 获取当前日期(如涉及时间)
2. 如需按分类筛选 → 调用 types 获取 typeId
3. 如需按账户筛选 → 调用 accounts 获取 accountId
4. 调用 flows 执行查询
```

### 流程 B:添加流水(最重要)

```
1. 调用 current_date 获取日期(用户未指定时)
2. 调用 accounts 获取 accountId
3. 调用 types 获取 typeId,同时检查该分类的 actionId
4. 如果 actionId != null → 直接使用
   如果 actionId == null → 调用 actions,根据用户的收支意图(handle)选择对应的 action
5. 单笔 → 调用 add_flow
   多笔(2 条及以上) → 调用 batch_add_flow,把所有条目组装成 JSON 数组一次性提交
```

### 流程 C:更新流水

```
1. 调用 flows 查询获取 flowId
2. 如需修改分类 → 调用 types,检查 actionId
3. 如果 actionId == null → 调用 actions
4. 调用 update_flow 更新
```

### 流程 D:导出 Excel

```
当流水超过 100 条,或用户明确要求导出时,调用 make_excel
返回的 downloadUrl 直接给用户
```

### 流程 E:查询系统信息和公告

```
1. 用户问"有什么公告/通知" → 调用 system_info notices
2. 用户问"系统版本/有没有更新/我的配置" → 调用 system_info version
3. 用户首次使用或问"系统状态" → 调用 system_info all
```

---

## 操作清单

所有 GET 类操作直接用 curl 调用,需要带 token header。token 从 `~/.config/easyaccounts/token` 读取。

### login(登录)

```bash
bash {baseDir}/scripts/login.sh <username> <password>
```

### current_date(获取当前日期)

不需要 API 调用,直接用 `date` 命令:

```bash
date '+%Y-%m-%d'
```

### accounts(查询账户列表)

```bash
TOKEN=$(cat ~/.config/easyaccounts/token)
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/account/getAccount" | jq '.'
```

返回所有账户的 id、名称、余额。

### types(获取分类列表)

```bash
TOKEN=$(cat ~/.config/easyaccounts/token)
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/type/getType" | jq '.'
```

返回分类层级结构。**重点检查每个分类的 `action.id`**:
- 不为 null → 这就是 actionId,直接用
- 为 null → 需要调用 actions 接口

### actions(获取收支动作列表)

```bash
TOKEN=$(cat ~/.config/easyaccounts/token)
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/action/getAction" \
  | jq '.data[] | select(.disable != true) | {id, hname, handle}'
```

只在 types 返回的 actionId 为 null 时调用。根据 handle(0=收入,1=支出,2=转账)选择对应的 action.id 作为 actionId。

### year_statistics(年度统计)

```bash
TOKEN=$(cat ~/.config/easyaccounts/token)
YEAR=2026
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/home/getHomeInfoV2/$YEAR" | jq '.'
```

### system_info(系统信息和公告)

合并了 `/home/getNotices` 和 `/home/getVersion` 两个接口,通过参数选择内容:

```bash
# 获取项目公告(用户问"有什么公告/通知/动态")
bash {baseDir}/scripts/system_info.sh notices

# 获取版本和系统配置(用户问"系统版本/有没有新版/我的登录配置")
bash {baseDir}/scripts/system_info.sh version

# 同时获取两者(默认,用户首次使用或问"系统状态")
bash {baseDir}/scripts/system_info.sh all
```

**notices 返回字段**(数组):
- `id` / `title` / `content` / `date`
- `url` — 相关链接(可能为 null)
- `expire` — 过期时间(可能为 null,null 表示永不过期)

**version 返回字段**(对象):
- `versions` — 各模块版本号:`fontBranch`(前端)、`backendBranch`(后端)、`mysqlBranch`、`agentBranch`、`webhookBranch`、`release`(总版本)、`versionCode`
- `auth` — 登录配置:`enable`、`expiredMinutes`(token 过期分钟数)、`singleLogin`(是否单点登录)
- `backup` — 数据库备份配置:`cron`、`valid`、`description`
- `update` — 云端更新检查:
  - 如果无更新:`{hasUpdate: false, message: "当前已是最新版本"}`
  - 如果有更新:`{hasUpdate: true, newVersion, newVersionCode, releaseDate, changelog, currentVersionCode}`,应主动告知用户可以升级

**使用场景**:
- 用户问"我用的是几版本" → version,回答 `release` 字段
- 用户问"有没有新版" → version,看 `update.hasUpdate`
- 用户问"项目有什么公告" → notices,把 title+content 列出来,有 url 的附上
- 用户问"系统怎么样/有什么消息" → all

### flows(查询流水)

参数复杂,使用 helper 脚本:

```bash
bash {baseDir}/scripts/query_flows.sh \
  --handle 1 \
  --start-date 2026-03-01 \
  --end-date 2026-03-31 \
  [--account-id 1] \
  [--types 5,8] \
  [--note 餐饮] \
  [--single-month true] \
  [--analysis true] \
  [--order-by 2]
```

handle 必填(0/1/2/3)。流水超过 100 条会自动截断,提示用 make_excel 导出。

### get_flow(获取单条流水详情)

```bash
TOKEN=$(cat ~/.config/easyaccounts/token)
FLOW_ID=123
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/flow/getFlow/$FLOW_ID" | jq '.'
```

### add_flow(添加流水)

使用 helper 脚本:

```bash
bash {baseDir}/scripts/add_flow.sh \
  --account-id 1 \
  --type-id 5 \
  --action-id 2 \
  --money 30.00 \
  --date 2026-04-01 \
  --note "公司午餐" \
  [--account-to-id 2] \
  [--collect false]
```

注意:`--money` 只传正数,系统自动处理正负。内部转账时必须传 `--account-to-id`。

### batch_add_flow(批量添加流水)

当用户一次提交多笔流水(如"记一下今天的:午餐30、地铁12、咖啡25"),用此脚本批量处理,**避免循环调用 add_flow.sh**(慢且无汇总)。

输入是 JSON 数组(通过文件或 stdin):

```bash
# 方式一:通过文件
bash {baseDir}/scripts/batch_add_flow.sh /tmp/flows.json

# 方式二:通过 stdin(推荐,无需临时文件)
cat <<'EOF' | bash {baseDir}/scripts/batch_add_flow.sh -
[
  {
    "accountId": 1,
    "typeId": 5,
    "actionId": 2,
    "money": "30.00",
    "fDate": "2026-04-01",
    "note": "公司午餐"
  },
  {
    "accountId": 1,
    "typeId": 8,
    "actionId": 2,
    "money": "12.00",
    "fDate": "2026-04-01",
    "note": "地铁"
  },
  {
    "accountId": 1,
    "typeId": 9,
    "actionId": 2,
    "money": "25.00",
    "fDate": "2026-04-01",
    "note": "咖啡"
  }
]
EOF
```

**输入字段**(同 add_flow):
- 必填:`accountId`、`typeId`、`actionId`、`money`、`fDate`
- 可选:`note`、`accountToId`(转账)、`collect`

**特性**:
- 单条失败不中断,继续处理后续条目
- 进度输出到 stderr(`✅`/`❌`),最终汇总 JSON 输出到 stdout
- 返回结构包含 `successCount`、`failedCount`、`successList`(含每条 flowId)、`failedList`(含失败原因)

**使用前提**:
- 多笔流水通常涉及不同分类,**先调用 types** 获取 typeId 和 actionId
- 如果不同笔涉及不同账户,先调用 accounts
- 同一批次的 createDate 相同,但 fDate 可不同

### update_flow(更新流水)

使用 helper 脚本:

```bash
bash {baseDir}/scripts/update_flow.sh \
  --flow-id 123 \
  --account-id 1 \
  --type-id 5 \
  --action-id 2 \
  --money 35.00 \
  --date 2026-04-01 \
  --note "公司午餐(改正)" \
  [--account-to-id 2] \
  [--collect false]
```

### make_excel(导出 Excel)

参数与 flows 类似,复用 query_flows.sh 的参数解析,但调用 `--export <文件名>`:

```bash
bash {baseDir}/scripts/query_flows.sh \
  --export "2026年3月账单" \
  --handle 1 \
  --start-date 2026-03-01 \
  --end-date 2026-03-31
```

返回 `downloadUrl`,直接展示给用户下载。

---

## 回复规范

- 金额保留 2 位小数
- 流水列表用简洁格式(ID/收支/金额/账户/分类/时间)
- 统计结果突出**收入、支出、盈余**三个数字
- 流水超 100 条时主动提示可用 make_excel 导出
- 涉及日期的操作前先调用 `date` 命令获取当前日期作为参考
- 写操作完成后,简短确认结果(包含 flowId,方便用户后续修改)

## 错误处理

- **HTTP 401 / code != 0**:可能是未登录或 token 过期,提示用户重新执行 login
- **缺少必要参数**:检查上下文,如不确定先调用相应的查询接口(accounts/types/actions)
- **分类不可用**:如果用户选了一级分类但它有子分类,提示用户选择具体的二级分类
