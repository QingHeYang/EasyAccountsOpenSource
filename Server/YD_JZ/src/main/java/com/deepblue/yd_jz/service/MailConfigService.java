package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.MailConfigResponseDto;
import com.deepblue.yd_jz.dto.MailConfigUpdateDto;
import com.deepblue.yd_jz.utils.CryptoUtils;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

// v2.7.0 (config-ui): 邮件配置语义层
// - get：读 DB（password 不回显）
// - update：null=不修改，非 null=覆盖，password 走 AES 加密；空串=清空
// - getDecryptedPassword：仅 MailService 内部用，把密文还原为明文喂给 SMTP
@Slf4j
@Service
public class MailConfigService {

    @Autowired
    private AppConfigService appConfigService;

    /** 读：给前端展示用，password 脱敏 */
    public MailConfigResponseDto getMaskedConfig() {
        MailConfigResponseDto dto = new MailConfigResponseDto();
        dto.setSmtpServer(get(SystemConfigConst.MAIL_SMTP_SERVER, ""));
        dto.setSmtpPort(get(SystemConfigConst.MAIL_SMTP_PORT, SystemConfigConst.MAIL_SMTP_PORT_DEFAULT));
        dto.setFromEmail(get(SystemConfigConst.MAIL_FROM_EMAIL, ""));
        dto.setPassword("");  // 永不回显密文/明文
        String pwdRaw = get(SystemConfigConst.MAIL_PASSWORD, "");
        dto.setIsPasswordSet(pwdRaw != null && !pwdRaw.isEmpty());
        dto.setToList(get(SystemConfigConst.MAIL_TO_LIST, ""));
        dto.setSendSqlBackup(parseBool(get(SystemConfigConst.MAIL_SEND_SQL_BACKUP,
                SystemConfigConst.MAIL_SEND_SQL_BACKUP_DEFAULT)));
        dto.setSendExcel(parseBool(get(SystemConfigConst.MAIL_SEND_EXCEL,
                SystemConfigConst.MAIL_SEND_EXCEL_DEFAULT)));
        return dto;
    }

    /** 更新：null=不修改；非 null=覆盖；password 空串=清空，非空=加密入库 */
    @Transactional(rollbackFor = Exception.class)
    public void update(MailConfigUpdateDto dto) {
        if (dto == null) return;

        if (dto.getSmtpServer() != null) {
            set(SystemConfigConst.MAIL_SMTP_SERVER, dto.getSmtpServer().trim());
        }
        if (dto.getSmtpPort() != null) {
            set(SystemConfigConst.MAIL_SMTP_PORT, dto.getSmtpPort().trim());
        }
        if (dto.getFromEmail() != null) {
            set(SystemConfigConst.MAIL_FROM_EMAIL, dto.getFromEmail().trim());
        }
        if (dto.getPassword() != null) {
            String trimmed = dto.getPassword();  // 密码不 trim，避免误改
            if (trimmed.isEmpty()) {
                set(SystemConfigConst.MAIL_PASSWORD, "");  // 清空
            } else {
                set(SystemConfigConst.MAIL_PASSWORD, CryptoUtils.aesEncrypt(trimmed));
            }
        }
        if (dto.getToList() != null) {
            set(SystemConfigConst.MAIL_TO_LIST, dto.getToList().trim());
        }
        if (dto.getSendSqlBackup() != null) {
            set(SystemConfigConst.MAIL_SEND_SQL_BACKUP, String.valueOf(dto.getSendSqlBackup()));
        }
        if (dto.getSendExcel() != null) {
            set(SystemConfigConst.MAIL_SEND_EXCEL, String.valueOf(dto.getSendExcel()));
        }
        log.info("mail config updated");
    }

    // ── 给 MailService（Phase 3）用的语义读方法 ──────────────────

    public String getSmtpServer()  { return get(SystemConfigConst.MAIL_SMTP_SERVER, ""); }
    public String getSmtpPort()    { return get(SystemConfigConst.MAIL_SMTP_PORT, SystemConfigConst.MAIL_SMTP_PORT_DEFAULT); }
    public String getFromEmail()   { return get(SystemConfigConst.MAIL_FROM_EMAIL, ""); }
    public String getToList()      { return get(SystemConfigConst.MAIL_TO_LIST, ""); }

    public boolean isSendSqlBackupEnabled() {
        return parseBool(get(SystemConfigConst.MAIL_SEND_SQL_BACKUP, SystemConfigConst.MAIL_SEND_SQL_BACKUP_DEFAULT));
    }

    public boolean isSendExcelEnabled() {
        return parseBool(get(SystemConfigConst.MAIL_SEND_EXCEL, SystemConfigConst.MAIL_SEND_EXCEL_DEFAULT));
    }

    /** 是否已配置完整可用的 SMTP（必填字段都非空） */
    public boolean isMailConfigured() {
        return notEmpty(getSmtpServer())
                && notEmpty(getSmtpPort())
                && notEmpty(getFromEmail())
                && notEmpty(getToList())
                && notEmpty(get(SystemConfigConst.MAIL_PASSWORD, ""));
    }

    /** 解密密码：仅给 MailService 用 */
    public String getDecryptedPassword() {
        String cipher = get(SystemConfigConst.MAIL_PASSWORD, "");
        return CryptoUtils.aesDecrypt(cipher);
    }

    // ── helpers ────────────────────────────────────────────

    private String get(String key, String defVal) {
        String v = appConfigService.getValue(SystemConfigConst.DOMAIN_MAIL, key);
        return v == null ? defVal : v;
    }

    private void set(String key, String val) {
        appConfigService.setValue(SystemConfigConst.DOMAIN_MAIL, key, val);
    }

    private static boolean parseBool(String v) {
        return "true".equalsIgnoreCase(v);
    }

    private static boolean notEmpty(String s) {
        return s != null && !s.isEmpty();
    }
}
