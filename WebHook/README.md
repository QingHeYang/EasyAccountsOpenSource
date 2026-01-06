# WebHook 服务

EasyAccounts 的 WebHook 服务模块，用于接收系统事件并执行自定义操作（如邮件通知）。

## 功能说明

当 EasyAccounts 后端触发特定事件时，会调用 WebHook 服务，目前支持以下功能：

| 事件类型 | 说明 | 邮件主题 |
|----------|------|----------|
| `sql_backup` | 数据库备份完成 | SQL 备份日志 |
| `month_excel` | 月度账单导出 | 月度 Excel 已生成 |
| `analysis_excel` | 财务分析导出 | 财务分析 Excel 已生成 |
| `screen_excel` | 筛选账单导出 | 筛选账单 Excel 已生成 |

## 技术栈

- Python 3.10+
- FastAPI
- SMTP 邮件发送

## 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SMTP_SERVER` | SMTP 服务器地址 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_MAIL` | 发件人邮箱 | `your@qq.com` |
| `SMTP_PASSWORD` | 邮箱授权码 | `xxxxxx` |
| `SMTP_TO_LIST` | 收件人列表（逗号分隔） | `a@mail.com,b@mail.com` |
| `SEND_SQL_BACKUP` | 是否发送 SQL 备份邮件 | `True` / `False` |
| `SEND_EXCEL` | 是否发送 Excel 邮件 | `True` / `False` |

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export SMTP_SERVER=smtp.qq.com
export SMTP_PORT=587
export SMTP_MAIL=your@qq.com
export SMTP_PASSWORD=your_password
export SMTP_TO_LIST=recipient@mail.com

# 启动服务
uvicorn webhook:app --host 0.0.0.0 --port 8083
```

## Docker 部署

```bash
# 构建镜像
docker build -t easyaccounts-webhook .

# 运行容器
docker run -d \
  --name webhook \
  -p 8083:8083 \
  -e SMTP_SERVER=smtp.qq.com \
  -e SMTP_PORT=587 \
  -e SMTP_MAIL=your@qq.com \
  -e SMTP_PASSWORD=your_password \
  -e SMTP_TO_LIST=recipient@mail.com \
  -e SEND_SQL_BACKUP=True \
  -e SEND_EXCEL=True \
  easyaccounts-webhook
```

## API 接口

### POST /webhook

接收文件并发送邮件通知。

**请求参数（multipart/form-data）：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | File | 附件文件 |
| `file_name` | string | 文件名 |
| `file_type` | string | 文件类型（sql_backup/month_excel/analysis_excel/screen_excel） |

**响应示例：**

```json
{
  "status": "ok",
  "result": "文件 xxx.xlsx 已发送到 ['a@mail.com']，发送结果：OK"
}
```

## 日志

日志文件：`hook.log`

## 注意事项

1. 使用 QQ 邮箱需要开启 SMTP 服务并获取授权码
2. 确保防火墙允许 8083 端口访问
3. 建议在 Docker 环境中运行，便于与其他服务集成
