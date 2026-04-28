package com.deepblue.yd_jz.service;

import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.FileSystemResource;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

// v2.7.0 (config-ui): EasyAccounts 站内统一邮件发送服务（替代 WebHook Python 容器）
//
// 设计要点：
//   1. 所有邮件统一抽象为 MailEnvelope（subject + summary + fields + advice + attachment + category）
//   2. 公共业务方法只填充 envelope；唯一私有 send(MailEnvelope) 负责前缀 / 字段格式 / 签名 / 全局开关 / SMTP
//   3. SMTP 参数每次发送前现读 MailConfigService（不重启即可生效）
//   4. 端口 465 自动走 SMTPS；其余端口走 STARTTLS（典型 587/25）
//   5. 业务事件邮件失败仅 log warn，不抛异常（不影响主流程）
//   6. 测试邮件返回 SendResult，把 SMTP 异常文本透出给前端
@Slf4j
@Service
public class MailService {

    private static final String SUBJECT_PREFIX = "[EasyAccounts] ";
    // 签名内嵌在 formatBody() HTML 页脚中，不再作为独立字符串

    private static final SimpleDateFormat DT_FMT = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

    /** 启动期一次性加载 logo 转 base64 data URI，避免每封邮件都读文件 */
    private static final String LOGO_DATA_URI = loadLogoDataUri();

    private static String loadLogoDataUri() {
        try (java.io.InputStream is = MailService.class.getResourceAsStream("/email/logo.png")) {
            if (is == null) return "";
            byte[] bytes = is.readAllBytes();
            return "data:image/png;base64," + java.util.Base64.getEncoder().encodeToString(bytes);
        } catch (Exception e) {
            log.warn("加载邮件 logo 失败，将使用纯文字头部: {}", e.getMessage());
            return "";
        }
    }

    // 邮件类别 —— 给 send() 内部判断全局开关
    public enum Category {
        SQL_BACKUP,         // 受 mail.send_sql_backup 开关控制
        EXCEL,              // 受 mail.send_excel 开关控制（覆盖月度/分析/筛选）
        SCHEDULED_REMINDER, // 由规则级 email_enabled 字段控制，本服务直发
        AUTO_EXCEL,         // 由 auto_excel.send_email 控制（生成成功 / 无流水）
        AUTO_EXCEL_REMIND,  // 由 auto_excel.remind_email_enabled 控制（提前提醒）
        TEST                // 测试，无开关
    }

    @Autowired
    private MailConfigService mailConfigService;

    // ── 业务语义入口（只负责填信封）─────────────────────────

    /** SQL 备份：自动调度 / 手动触发后调用 */
    public void sendSqlBackup(File backupFile) {
        send(MailEnvelope.builder()
                .category(Category.SQL_BACKUP)
                .subject("SQL 备份完成")
                .summary("您的 EasyAccounts 数据库已自动备份完成。")
                .field("备份时间", now())
                .field("备份文件", backupFile.getName())
                .field("文件大小", humanFileSize(backupFile))
                .advice("附件即为本次备份，请妥善保存。建议同时存储到本机以外的位置（如云盘 / 邮箱归档），以应对硬盘损坏、误操作等数据丢失风险。")
                .attachment(backupFile)
                .build());
    }

    /** 月度账单 Excel 导出 */
    public void sendMonthExcel(File excel, String period) {
        send(MailEnvelope.builder()
                .category(Category.EXCEL)
                .subject(safe(period, "月度账单") + " 月度账单")
                .summary("您的 " + safe(period, "月度") + " 账单 Excel 已生成。")
                .field("生成时间", now())
                .field("文件名称", excel.getName())
                .field("数据周期", safe(period, "（未指定）"))
                .advice("附件为本期完整流水及账户余额，包含分类汇总、收支结余等。")
                .attachment(excel)
                .build());
    }

    /** 财务分析 Excel 导出 */
    public void sendAnalysisExcel(File excel, String dateRange) {
        send(MailEnvelope.builder()
                .category(Category.EXCEL)
                .subject("财务分析导出")
                .summary("您的财务分析 Excel 已生成。")
                .field("生成时间", now())
                .field("文件名称", excel.getName())
                .field("分析区间", safe(dateRange, "（未指定）"))
                .advice("附件包含趋势分析、分类占比、账户对比等数据。")
                .attachment(excel)
                .build());
    }

    /** 筛选账单 Excel 导出（筛选条件复杂多变，邮件正文不展示，详情看附件） */
    public void sendScreenExcel(File excel) {
        send(MailEnvelope.builder()
                .category(Category.EXCEL)
                .subject("筛选账单导出")
                .summary("您筛选的账单 Excel 已生成。")
                .field("生成时间", now())
                .field("文件名称", excel.getName())
                .advice("附件为符合筛选条件的全部流水，详细条件见 Excel 表头。")
                .attachment(excel)
                .build());
    }

    /** 定时记账事前提醒。调用方传结构化数据，统一 envelope 模式 */
    public void sendScheduledReminder(String ruleName, String summary,
                                      java.util.LinkedHashMap<String, String> fields,
                                      String advice) {
        MailEnvelope.Builder b = MailEnvelope.builder()
                .category(Category.SCHEDULED_REMINDER)
                .subject("定时记账提醒：" + ruleName)
                .summary(summary)
                .advice(advice);
        if (fields != null) fields.forEach(b::field);
        send(b.build());
    }

    /** 自动月度 Excel：当月无流水，跳过生成。无附件邮件 */
    public void sendAutoExcelNoFlow(String yearMonth) {
        send(MailEnvelope.builder()
                .category(Category.AUTO_EXCEL)
                .subject(yearMonth + " 月度账单：本月无流水")
                .summary("您的 " + yearMonth + " 月账单 Excel 自动生成已跳过，因当月没有任何流水记录。")
                .field("跳过时间", now())
                .field("数据周期", yearMonth)
                .advice("如果这与您的实际情况不符，请检查是否漏记或晚记了流水，下次自动生成将在配置的下个执行日。")
                .build());
    }

    /** 自动月度 Excel 提前提醒；调用方传结构化数据 */
    public void sendAutoExcelReminder(String yearMonth, String summary,
                                      java.util.LinkedHashMap<String, String> fields,
                                      String advice) {
        MailEnvelope.Builder b = MailEnvelope.builder()
                .category(Category.AUTO_EXCEL_REMIND)
                .subject("自动生成账单提醒：" + yearMonth)
                .summary(summary)
                .advice(advice);
        if (fields != null) fields.forEach(b::field);
        send(b.build());
    }

    /** 测试发邮件按钮：把异常文本透出给前端 */
    public SendResult sendTestMail() {
        if (!mailConfigService.isMailConfigured()) {
            return SendResult.fail("SMTP 配置不完整，请先填写服务器地址、发件邮箱、密码、收件人");
        }
        try {
            sendInternal(MailEnvelope.builder()
                    .category(Category.TEST)
                    .subject("邮件配置测试")
                    .summary("如果您看到这封邮件，说明 EasyAccounts 的 SMTP 配置正确。系统将按您的设置发送 SQL 备份、Excel 导出、定时记账提醒等邮件。")
                    .field("测试时间", now())
                    .field("发件邮箱", mailConfigService.getFromEmail())
                    .field("收件人列表", mailConfigService.getToList())
                    .build());
            return SendResult.ok("邮件已发送到：" + mailConfigService.getToList());
        } catch (Exception e) {
            log.warn("test mail failed: {}", e.getMessage());
            return SendResult.fail(e.getMessage());
        }
    }

    // ── 唯一发送入口（业务侧静默） ──────────────────────────

    private void send(MailEnvelope env) {
        // 全局开关
        if (!isCategoryEnabled(env.getCategory())) {
            log.debug("category {} 关闭，跳过 [{}]", env.getCategory(), env.getSubject());
            return;
        }
        if (!mailConfigService.isMailConfigured()) {
            log.warn("SMTP 配置不完整，跳过邮件 [{}]", env.getSubject());
            return;
        }
        try {
            sendInternal(env);
        } catch (Exception e) {
            log.warn("发送邮件失败 [{}]: {}", env.getSubject(), e.getMessage());
        }
    }

    private boolean isCategoryEnabled(Category cat) {
        switch (cat) {
            case SQL_BACKUP:         return mailConfigService.isSendSqlBackupEnabled();
            case EXCEL:              return mailConfigService.isSendExcelEnabled();
            case SCHEDULED_REMINDER: return true;  // 由规则级开关控制，到这里说明该发
            case AUTO_EXCEL:         return true;  // 由 auto_excel.send_email 控制，业务层已决定，到这里就发
            case AUTO_EXCEL_REMIND:  return true;  // 由 auto_excel.remind_email_enabled 控制，同上
            case TEST:               return true;
            default: return true;
        }
    }

    private void sendInternal(MailEnvelope env) throws Exception {
        JavaMailSenderImpl sender = buildSender();
        MimeMessage mime = sender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mime, env.getAttachment() != null, "UTF-8");

        helper.setFrom(new InternetAddress(mailConfigService.getFromEmail()));
        helper.setTo(parseRecipients(mailConfigService.getToList()));
        helper.setSubject(SUBJECT_PREFIX + env.getSubject());
        helper.setText(formatBody(env), true);  // true = HTML

        if (env.getAttachment() != null && env.getAttachment().exists()) {
            helper.addAttachment(env.getAttachment().getName(),
                    new FileSystemResource(env.getAttachment()));
        }

        sender.send(mime);
        log.info("mail sent: subject=[{}], to={}", env.getSubject(), mailConfigService.getToList());
    }

    /**
     * 统一正文格式（HTML）：品牌色头部 + summary 段落 + 字段表 + 提示框 + 页脚签名
     * 所有客户端只用内联样式 + table 布局，避免 Outlook / QQ 邮箱渲染差异。
     */
    private static String formatBody(MailEnvelope env) {
        StringBuilder sb = new StringBuilder();
        sb.append("<!DOCTYPE html><html><head>")
          .append("<meta charset=\"UTF-8\">")
          .append("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
          .append("</head>");
        sb.append("<body style=\"margin:0;padding:0;background-color:#f5f7fa;")
          .append("font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#333;\">");

        // 外层壳：浅灰背景；padding 移动端缩小
        sb.append("<table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" ")
          .append("style=\"background-color:#f5f7fa;padding:16px 8px;\"><tr><td align=\"center\">");

        // 内层卡片：响应式 max-width，移动端铺满
        sb.append("<table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" ")
          .append("style=\"width:100%;max-width:640px;background-color:#ffffff;border-radius:8px;")
          .append("overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);\">");

        // 头部 —— logo + 文字横排
        sb.append("<tr><td style=\"background-color:#4F8EF7;padding:20px 24px;color:#ffffff;\">");
        sb.append("<table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" style=\"width:100%;\"><tr>");
        if (!LOGO_DATA_URI.isEmpty()) {
            sb.append("<td width=\"56\" style=\"vertical-align:middle;padding-right:14px;\">")
              .append("<img src=\"").append(LOGO_DATA_URI).append("\" ")
              .append("width=\"48\" height=\"48\" alt=\"EasyAccounts\" ")
              .append("style=\"display:block;width:48px;height:48px;border-radius:8px;background:#fff;\">")
              .append("</td>");
        }
        sb.append("<td style=\"vertical-align:middle;\">")
          .append("<div style=\"font-size:20px;font-weight:600;letter-spacing:0.5px;line-height:1.3;\">EasyAccounts</div>")
          .append("<div style=\"font-size:13px;opacity:0.92;margin-top:4px;line-height:1.4;\">")
          .append(htmlEscape(env.getSubject()))
          .append("</div></td>");
        sb.append("</tr></table>");
        sb.append("</td></tr>");

        // 正文区 —— 移动端 padding 缩小
        sb.append("<tr><td style=\"padding:24px 20px;\">");

        // summary
        if (env.getSummary() != null && !env.getSummary().isEmpty()) {
            sb.append("<p style=\"margin:0 0 24px 0;font-size:15px;line-height:1.7;color:#2c3e50;\">")
              .append(htmlEscape(env.getSummary()))
              .append("</p>");
        }

        // 字段表
        if (env.getFields() != null && !env.getFields().isEmpty()) {
            sb.append("<table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" ")
              .append("style=\"border-collapse:collapse;margin:0 0 24px 0;border:1px solid #e9ecef;\">");
            for (Map.Entry<String, String> e : env.getFields().entrySet()) {
                sb.append("<tr>")
                  .append("<td style=\"padding:12px 16px;background-color:#f8f9fa;border-bottom:1px solid #e9ecef;")
                  .append("width:30%;color:#6c757d;font-size:14px;vertical-align:top;\">")
                  .append(htmlEscape(e.getKey()))
                  .append("</td>")
                  .append("<td style=\"padding:12px 16px;background-color:#ffffff;border-bottom:1px solid #e9ecef;")
                  .append("color:#2c3e50;font-size:14px;\">")
                  .append(htmlEscape(e.getValue()))
                  .append("</td></tr>");
            }
            sb.append("</table>");
        }

        // 提示框
        if (env.getAdvice() != null && !env.getAdvice().isEmpty()) {
            sb.append("<table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" ")
              .append("style=\"background-color:#fff7e6;border-left:4px solid #ffa940;margin-bottom:8px;\">")
              .append("<tr><td style=\"padding:14px 18px;font-size:13px;line-height:1.6;color:#874d00;\">")
              .append("<strong style=\"color:#d46b08;\">💡 提示</strong>&nbsp;&nbsp;")
              .append(htmlEscape(env.getAdvice()))
              .append("</td></tr></table>");
        }

        sb.append("</td></tr>");

        // 页脚
        sb.append("<tr><td style=\"border-top:1px solid #e9ecef;padding:16px 20px;text-align:center;")
          .append("font-size:12px;color:#adb5bd;line-height:1.6;\">")
          .append("—— EasyAccounts 记账助手 ——<br>")
          .append("本邮件由系统自动发送，请勿回复")
          .append("</td></tr>");

        // 关闭壳
        sb.append("</table></td></tr></table></body></html>");
        return sb.toString();
    }

    /** HTML 转义，防止字段值里的 &lt; / &amp; 等破坏渲染 */
    private static String htmlEscape(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }

    /** 每次发送前根据当前 DB 配置构建 sender；不缓存为 Bean，保证配置改动即时生效 */
    private JavaMailSenderImpl buildSender() {
        JavaMailSenderImpl sender = new JavaMailSenderImpl();
        sender.setHost(mailConfigService.getSmtpServer());
        int port = parsePort(mailConfigService.getSmtpPort());
        sender.setPort(port);
        sender.setUsername(mailConfigService.getFromEmail());
        sender.setPassword(mailConfigService.getDecryptedPassword());
        sender.setDefaultEncoding("UTF-8");

        Properties props = sender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        if (port == 465) {
            // 端口 465：SMTPS（隐式 SSL）
            props.put("mail.smtp.ssl.enable", "true");
        } else {
            // 其他端口（典型 587/25）：STARTTLS（显式升级）
            props.put("mail.smtp.starttls.enable", "true");
            props.put("mail.smtp.starttls.required", "true");
        }
        props.put("mail.smtp.connectiontimeout", "60000");
        props.put("mail.smtp.timeout", "60000");
        props.put("mail.smtp.writetimeout", "60000");
        return sender;
    }

    private static String[] parseRecipients(String toList) {
        if (toList == null || toList.trim().isEmpty()) return new String[0];
        String[] parts = toList.split(",");
        for (int i = 0; i < parts.length; i++) parts[i] = parts[i].trim();
        return parts;
    }

    private static int parsePort(String s) {
        try { return Integer.parseInt(s.trim()); } catch (Exception e) { return 465; }
    }

    private static String now() {
        return DT_FMT.format(new Date());
    }

    private static String humanFileSize(File f) {
        if (f == null || !f.exists()) return "—";
        long bytes = f.length();
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        return String.format("%.1f MB", bytes / 1024.0 / 1024.0);
    }

    private static String safe(String s, String fallback) {
        return (s == null || s.isEmpty()) ? fallback : s;
    }

    // ── 数据结构 ──────────────────────────────────────────

    /** 邮件信封：抽象一封邮件的全部内容；用 builder 填充，不可变 */
    @Data
    public static class MailEnvelope {
        private final Category category;
        private final String subject;
        private final String summary;
        private final Map<String, String> fields;
        private final String advice;
        private final File attachment;

        private MailEnvelope(Builder b) {
            this.category = b.category;
            this.subject = b.subject;
            this.summary = b.summary;
            this.fields = b.fields;
            this.advice = b.advice;
            this.attachment = b.attachment;
        }

        public static Builder builder() { return new Builder(); }

        public static class Builder {
            private Category category = Category.TEST;
            private String subject;
            private String summary;
            private final Map<String, String> fields = new LinkedHashMap<>();
            private String advice;
            private File attachment;

            public Builder category(Category c)       { this.category = c; return this; }
            public Builder subject(String s)          { this.subject = s; return this; }
            public Builder summary(String s)          { this.summary = s; return this; }
            public Builder field(String k, String v)  { this.fields.put(k, v); return this; }
            public Builder advice(String s)           { this.advice = s; return this; }
            public Builder attachment(File f)         { this.attachment = f; return this; }
            public MailEnvelope build()               { return new MailEnvelope(this); }
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SendResult {
        private boolean success;
        private String message;

        public static SendResult ok(String msg)   { return new SendResult(true, msg); }
        public static SendResult fail(String msg) { return new SendResult(false, msg); }
    }
}
