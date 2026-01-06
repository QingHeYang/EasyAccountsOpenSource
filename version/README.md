# 版本分支管理记录

本目录用于记录各版本的发布信息和分支合并情况。

---

## 2.6.0 版本

### Feature 分支合并记录

| 分支名 | 状态 | 合并日期 | 说明 |
|--------|------|----------|------|
| `2.6.0-server-upgrade` | ✅ 已合并 | 2026-01-05 | Spring Boot 3.x 框架升级 |
| `2.6.0-VL` | ✅ 已合并 | 2026-01-01 | VL 多模态图片识别记账 |
| `2.6.0-EH` | 🔄 开发中 | - | API 错误处理优化 |

### 2.6.0-server-upgrade 分支内容

**核心升级：**
- Spring Boot 2.4.11 → 3.x
- Java 11 → 17
- javax.* → jakarta.* 命名空间迁移
- Swagger → SpringDoc OpenAPI

**配置调整：**
- 删除 `application-dev.properties`
- 删除 `application-windows.properties`
- 合并为统一的 `application-server.properties`
- 新增 `application-local.properties.example` 本地开发示例

**Excel 模板升级：**
- `.xls` → `.xlsx` 格式
- ExcelService 适配 Apache POI XSSF

**新增功能：**
- 净资产（netAsset）与不计入总金额（exemptAsset）功能
- 看板页面净资产显示优化

**相关文档：**
- `Server/docs/feature-guide/upgrade-spring-boot-3-guide.md`
- `Server/docs/feature-guide/upgrade-spring-boot-3-progress.md`
- `Server/docs/feature-guide/excel-style-enhancement-dev-log.md`
- `Server/docs/dev-guide/exempt_不计入总金额设计.md`

### 2.6.0-VL 分支内容

**功能说明：** VL (Vision-Language) 多模态支持，用户可上传图片（票据、账单截图），AI 识别后自动记账。

**核心提交：**
```
4bd21e9 feat(ai): 完成 VL 图片附件功能
a098c65 feat(ai): add_flow/update_flow 支持图片附件
ab0e7ad docs(ai): 更新工具描述和提示词，添加图片附件说明
f6fad03 revert(ai): 移除 add_flow/update_flow 的 images 参数
```

**技术实现：**
- 新增 `Attachment` 模型，支持图片 Base64 存储
- `Message.to_llm_content()` 方法转换为 OpenAI VL 格式
- 支持 GPT-4V、DeepSeek-VL 等多模态模型
- 前端图片上传组件

**相关文档：**
- `ai/KoalaqHub/docs/feature-guide/VL_改动方案.md`
- `ai/KoalaqHub/docs/dev-guide/VL_运行流程.md`

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `x.x.x.json` | 版本发布时的详细信息（功能清单、变更记录等） |
| `README.md` | 分支合并记录和版本开发状态 |
