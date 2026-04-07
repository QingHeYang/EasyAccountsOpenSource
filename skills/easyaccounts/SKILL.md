---
name: easyaccounts
description: 家庭财务管家 / Family finance manager. 通过自然语言对接 EasyAccounts 个人记账系统,支持记账、查账、批量记账、内部转账、流水修改、收支统计、年度分析、Excel 导出、系统公告查询等。Manage household accounts, expenses, income, transfers, statistics and reports for EasyAccounts (a self-hosted personal finance/bookkeeping system with MySQL backend).
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

## 不支持的操作(明确告知用户)

- **删除流水**:本 skill **不提供**删除功能(高风险不可逆操作)。用户要求删除时,引导用户**到前端 EasyAccounts 网页/桌面端手动删除**(前端删除会同步恢复账户余额)
- **删除账户、分类、动作**:同上,只读不删
- **创建账户、分类、动作**:本 skill 不涉及主数据维护,引导用户去前端

---

## 准备工作

### 环境变量(用户配置在 `~/.openclaw/.env`)

| 变量 | 必需 | 说明 |
|------|------|------|
| `EASYACCOUNTS_URL` | ✅ | 后端地址,如 `http://localhost:8081` 或带 nginx 代理路径 `http://example.com/api` |
| `EASYACCOUNTS_USERNAME` | ❌ | 仅服务端开启登录时需要 |
| `EASYACCOUNTS_PASSWORD` | ❌ | 同上,脚本自动 MD5 |

### 认证(LLM 通常无需关心)

- **未开启登录** → 直接调用,无需任何凭据
- **开启登录 + env 有凭据** → 401 时自动登录、缓存 token、无感重试
- **开启登录 + env 无凭据** → 操作返回 `认证失败(HTTP 401)`,LLM 向用户索要账号密码后调 `login.sh <username> <password>`,再重试原操作

**LLM 不要默认就调 login.sh,也不要硬编码密码。**

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

## ⚠️ JSON 字段名(后端 Lombok+Jackson 序列化坑)

**同一概念在不同接口里有 3 套命名**,根源是后端有的接口返回 DTO(用了 `name`),有的接口返回 entity(用 `aName` → 序列化为 `aname`),还有的用了自定义字段名(`accountName`)。LLM 必须按接口选字段名,**不能跨接口套用**:

### 速查表

| 概念 | `/account/getAccount` (DTO) | flows 列表 / get_flow 嵌套 / types (entity) | year_statistics 嵌套 |
|------|------------------------------|---------------------------------------------|----------------------|
| 账户名 | `name` | `aname`(小写) | `accountName` |
| 分类名 | — | `tname`(小写) | — |
| 动作名 | — | `hname`(小写) | — |
| 日期 | — | `fdate`(小写) | — |
| 转入账户名 | — | `toAName`(驼峰,转账时有值) | — |

**特别注意**:`get_flow` 接口里的嵌套 `account` 对象**走 entity 路径**,字段是 `aname` 不是 `name`!跟 `/account/getAccount` 不一样。

**记忆法**:Java 字段 `aName` → JSON `aname`(小写),`name` → JSON `name`(原样),`accountName` → JSON `accountName`(原样)。

### accounts 接口(`/account/getAccount`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 账户 ID |
| `name` | string | 账户名 |
| `money` | string | 余额 |
| `exemptMoney` | string | 免计金额 |
| `accountType` | int | 0=资产,1=负债 |
| `note` | string | 备注 |
| `card` | string | 卡号 |

### flows 列表接口(`/screen/getFlowByScreen`)

返回**扁平字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 流水 ID |
| `aname` | string | 账户名 |
| `tname` | string | 分类名 |
| `hname` | string | 收支动作名("支出"/"收入"等) |
| `handle` | int | 0=收入 1=支出 2=转账 |
| `money` | string | 金额 |
| `fdate` | string | 流水日期 |
| `note` | string | 备注 |
| `toAName` | string | 转入账户名(转账时有) |
| `from` | string | 来源标记 |
| `collect` | bool | 是否收藏 |
| `hasImages` | bool | 是否有图片 |
| `exempt` | bool | 是否免计 |

### get_flow 详情接口(`/flow/getFlow/{id}`)

返回**嵌套对象**(注意!跟列表接口结构完全不一样,也跟 `/account/getAccount` 字段名不一样):

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `money` / `fdate` / `note` / `from` / `collect` | 同列表 | 扁平字段 |
| `account` | object | 源账户(entity 序列化):`{id, aname, money(余额), exemptMoney, card, accountType, note}` ⚠️ **是 `aname` 不是 `name`** |
| `accountTo` | object | 转入账户(转账时有),字段同 account |
| `type` | object | `{id, tname, parent, action(嵌套), childrenTypes, hasChild, ...}` |
| `action` | object | `{id, handle, hname, exempt, exemptMode, disable}` |
| `images` | array | 图片 URL 列表(可能为 null) |

### types 接口(`/type/getType`)

| 字段 | 说明 |
|------|------|
| `id` | 分类 ID(**这就是 typeId**) |
| `tname` | 分类名 |
| `action` | 嵌套对象 `{id, handle, hname}` 或 **null**(分类未绑定 action) |
| `childrenTypes` | 子分类列表(有则一级分类不可用,需选子) |

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

**重要细节**:
- **金额规范化**:用户的金额可能带"块"、"元"、"块钱"等单位或符号,LLM 应解析成纯数字。如"30 块" → `30.00`,"一百二" → `120.00`
- **createDate 不需要传**:helper 脚本自动设置当前时间
- **内部转账(转账给自己的另一个账户)请走【流程 G】**,需要 `accountToId`
- **金额只传正数**:即便用户说"花了 30",也是传 `30` 不是 `-30`,系统根据 actionId 自动定方向

### 流程 C:更新流水

```
1. 调用 flows 查询获取 flowId
2. 如需修改分类 → 调用 types,检查 actionId
3. 如果 actionId == null → 调用 actions
4. 调用 update_flow 更新
```

### 流程 D:导出 Excel(基于查询)

```
1. 总是先调用 query_flows 查询(看一眼数量和数据)
2. 检查返回字段:
   - is_truncated == false 且数量较少 → 直接展示给用户,不需要导出
   - is_truncated == true(>100 条) → 主动告知"共 X 条,只展示了前 100 条,可导出 Excel"
3. 用户确认导出 → 用相同的查询参数 + --export "<文件名>" 调 query_flows
4. 文件生成在服务器 Resource/excel/screen/ 目录(脚本返回 fileName)
5. **没有直接的 downloadUrl**,告诉用户:"文件已生成在服务器,请到前端下载页面或让运维拷贝"
```

### 流程 E:查询系统信息和公告

```
1. 用户问"有什么公告/通知" → 调用 system_info notices
2. 用户问"系统版本/有没有更新/我的配置" → 调用 system_info version
3. 用户首次使用或问"系统状态" → 调用 system_info all
```

⚠️ notices 返回的公告中可能含**已过期**的(`expire` 字段不为 null 且早于今天),LLM 应**主动跳过**,不要展示给用户。

### 流程 F:删除流水(本 skill 不支持)

```
用户要求删除时:
1. 不要调用任何 API
2. 直接告知:"出于安全考虑,本 skill 不支持删除流水。请到前端 EasyAccounts 网页/桌面端手动删除,前端会自动恢复账户余额。"
3. 如果用户只是想"撤销错误的记账",建议改用 update_flow 修改金额或备注
```

### 流程 G:内部转账(handle=2,与普通收支不同)

```
用户场景:"从微信转 500 到银行卡"、"工资转入理财账户"
1. 调用 accounts 拿到源账户和目标账户的 ID
2. 调用 actions,找 handle == 2 的动作(通常名为"内部转账")
3. typeId 选用一个转账类目(通常是某个被标记为 handle=2 的分类),
   或如果没有专属转账类目,可以复用普通分类(具体看你的 EasyAccounts 数据)
4. 调用 add_flow,**必须**传 `--account-to-id <目标账户ID>`
5. 金额仍然只传正数,后端自动处理"源账户 -money,目标账户 +money"
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
curl -s -H "authorization: $TOKEN" "$EASYACCOUNTS_URL/home/getHomeInfoV2/$YEAR" | jq '.data'
```

**返回字段**:

| 字段 | 说明 |
|------|------|
| `totalAsset` | 总资产 |
| `netAsset` | 净资产(总资产 - 负债) |
| `yearIncome` | 该年总收入 |
| `yearOutCome` | 该年总支出 |
| `yearBalance` | 该年盈余(收入 - 支出) |
| `curIncome` | 当月收入(只在查询当年时有值,跨年查询为 null) |
| `curOutCome` | 当月支出(同上) |
| `accounts` | 数组,各账户资产明细 |
| `monthDetails` | 数组,各月详情 |

**`accounts` 子字段**(注意!**第三种账户名命名**):

| 子字段 | 说明 |
|--------|------|
| `id` | 账户 ID |
| `accountName` | 账户名(**注意:不是 `name` 也不是 `aname`**) |
| `accountAsset` | 账户资产值 |
| `exemptAsset` | 免计资产 |
| `percent` | 占总资产百分比 |
| `accountType` | 0=资产,1=负债 |
| `note` | 备注 |

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

⚠️ **LLM 必须主动过滤过期公告**:`expire` 不为 null 且早于今天的公告**不要展示**。如不确定今天日期,先调用 current_date(`date '+%Y-%m-%d'`)。

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

**参数说明**:

| 参数 | 必填 | 说明 |
|------|------|------|
| `--handle` | ✅ | 0=收入 1=支出 2=转账 3=全部 |
| `--start-date` | ❌ | 开始日期 yyyy-MM-dd |
| `--end-date` | ❌ | 结束日期 yyyy-MM-dd |
| `--single-month true` | ❌ | 单月查询模式,只需 start-date(取该月任意日期),省略 end-date |
| `--account-id N` | ❌ | 按账户筛选,先用 accounts 拿 ID |
| `--types 5,8` | ❌ | **分类 ID 列表**(逗号分隔),不是分类名!需先调 types 拿 ID |
| `--note 餐饮` | ❌ | **单个**关键字,模糊匹配备注(不支持多关键字 AND/OR) |
| `--analysis true` | ❌ | 返回每条流水占总收入/支出的百分比 |
| `--order-by N` | ❌ | 0=金额升序 1=金额降序 2=时间升序;**默认按时间倒序(最新在前)** |

**返回字段**:

| 字段 | 说明 |
|------|------|
| `summary` | 汇总字符串"收入=X,支出=Y,盈余=Z" |
| `flows` | 格式化的流水字符串数组(每条形如 `流水ID:N;收支:Y;金额:Z;...`) |
| `total_count` | 符合条件的总数(截断前) |
| `returned_count` | 实际返回数量 |
| `is_truncated` | bool,**true 表示超过 100 条被截断** |
| `notice` | 截断时的提示消息 |

**截断规则**:超过 100 条时,**保留按当前排序的前 100 条**(默认时间倒序即最新的)。剩余数据**无法**通过 flows 获取,**必须**用 make_excel 导出完整数据。LLM 应主动提醒用户。

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

**参数说明**:
- `--money`:**只传正数**,系统根据 actionId 的 handle 自动处理正负
- `--account-to-id`:**仅** handle=2(内部转账)时传,其他情况不要传
- `--note`:用户的备注。脚本内部会自动追加来源标识,LLM 不需要管
- `--collect`:可选,默认 false
- **不需要传 createDate**,脚本自动设置当前时间

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

**返回字段**:
- `success`:bool
- `fileName`:生成的实际文件名(含时间戳后缀)
- `notice`:提示文本

⚠️ **没有 downloadUrl 字段**。文件生成在服务器 `Resource/excel/screen/` 目录,需要用户:
- 通过 EasyAccounts 前端的下载页面获取
- 或联系运维拷贝

LLM 应该把 `fileName` + `notice` 一起告诉用户,**不要承诺给链接**。

---

## 回复规范

- 金额保留 2 位小数
- 流水列表用简洁格式(ID/收支/金额/账户/分类/时间)
- 统计结果突出**收入、支出、盈余**三个数字
- 流水超 100 条时主动提示可用 make_excel 导出
- 涉及日期的操作前先调用 `date` 命令获取当前日期作为参考
- 写操作完成后,简短确认结果(包含 flowId,方便用户后续修改)

## 错误处理

- **HTTP 401**:服务端开启了登录但未提供 token,或 token 已过期(默认 30 分钟)。引导用户提供账号密码后调 login.sh,然后重试
- **业务错误 code != 0**:看 msg 字段,通常是参数错误或业务规则限制
- **缺少必要参数**:不要瞎猜,先调用对应的查询接口(accounts/types/actions/flows)拿到准确 ID
- **分类不可用**:LLM 选了有子分类的一级分类,后端会拒绝。重新让用户从子分类里选
- **删除请求**:本 skill 不支持,引导前端处理(见【流程 F】)
- **批量操作部分失败**:batch_add_flow 返回的 `failedList` 含失败索引和原因,LLM 应总结哪些条成功、哪些失败,失败的让用户决定是否手动重试
