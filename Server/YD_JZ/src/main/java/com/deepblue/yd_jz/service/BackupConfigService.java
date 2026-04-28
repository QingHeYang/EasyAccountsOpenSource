package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.BackupConfigResponseDto;
import com.deepblue.yd_jz.dto.BackupConfigUpdateDto;
import com.deepblue.yd_jz.event.BackupConfigChangedEvent;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.CronBuilder;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Set;

// v2.7.0 (config-ui): 备份配置语义层
// - get：读 5 字段 + 拼 cron 一并返回
// - update：null=不修改；校验通过后入库；调度热重载留 Phase 4 接上
// - getCron：给 SQLBackUpTask 现读使用
// - isEnabled：给 SQLBackUpTask 决定是否安排任务
@Slf4j
@Service
public class BackupConfigService {

    private static final Set<String> VALID_FREQ = Set.of(
            SystemConfigConst.FREQ_DAILY,
            SystemConfigConst.FREQ_WEEKLY,
            SystemConfigConst.FREQ_MONTHLY);

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    /** 读：含 cron 一并展示 */
    public BackupConfigResponseDto get() {
        BackupConfigResponseDto dto = new BackupConfigResponseDto();
        dto.setEnabled(isEnabled());
        dto.setFrequency(getFrequency());
        dto.setTime(getTime());
        dto.setDayOfWeek(getDayOfWeek());
        dto.setDayOfMonth(getDayOfMonth());
        try {
            dto.setCron(CronBuilder.build(dto.getFrequency(), dto.getTime(),
                    dto.getDayOfWeek(), dto.getDayOfMonth()));
        } catch (Exception e) {
            // 配置非法时不阻断读取，cron 字段留空让前端意识到
            dto.setCron("");
        }
        return dto;
    }

    /**
     * 更新：null=不修改；落库后预留调度热重载（Phase 4 实现）
     */
    @Transactional(rollbackFor = Exception.class)
    public void update(BackupConfigUpdateDto dto) {
        if (dto == null) return;

        // 先把"目标值"算出来（已传字段用新值，未传字段用 DB 现值），整体校验后再入库
        Boolean enabled = dto.getEnabled() != null ? dto.getEnabled() : isEnabled();
        String frequency = dto.getFrequency() != null ? dto.getFrequency().trim() : getFrequency();
        String time = dto.getTime() != null ? dto.getTime().trim() : getTime();
        Integer dow = dto.getDayOfWeek() != null ? dto.getDayOfWeek() : getDayOfWeek();
        Integer dom = dto.getDayOfMonth() != null ? dto.getDayOfMonth() : getDayOfMonth();

        // 校验
        if (!VALID_FREQ.contains(frequency)) {
            throw new BusinessException(ErrorCode.PARAM_INVALID,
                    "frequency 仅支持 daily / weekly / monthly");
        }
        // 调用 CronBuilder 校验 time / dow / dom（拼出来的 cron 暂不存，每次现拼）
        CronBuilder.build(frequency, time, dow, dom);

        // 全部合法，入库
        set(SystemConfigConst.BACKUP_ENABLED, String.valueOf(enabled));
        set(SystemConfigConst.BACKUP_FREQUENCY, frequency);
        set(SystemConfigConst.BACKUP_TIME, time);
        set(SystemConfigConst.BACKUP_DAY_OF_WEEK, String.valueOf(dow));
        set(SystemConfigConst.BACKUP_DAY_OF_MONTH, String.valueOf(dom));

        log.info("backup config updated: enabled={}, freq={}, time={}, dow={}, dom={}",
                enabled, frequency, time, dow, dom);

        // Phase 4：发事件触发 SQLBackUpTask.reload() 实现热生效
        eventPublisher.publishEvent(new BackupConfigChangedEvent(this));
    }

    // ── 语义读 ─────────────────────────────────────────────

    public boolean isEnabled() {
        return parseBool(get(SystemConfigConst.BACKUP_ENABLED, SystemConfigConst.BACKUP_ENABLED_DEFAULT));
    }

    public String getFrequency() {
        return get(SystemConfigConst.BACKUP_FREQUENCY, SystemConfigConst.BACKUP_FREQUENCY_DEFAULT);
    }

    public String getTime() {
        return get(SystemConfigConst.BACKUP_TIME, SystemConfigConst.BACKUP_TIME_DEFAULT);
    }

    public Integer getDayOfWeek() {
        return parseInt(get(SystemConfigConst.BACKUP_DAY_OF_WEEK, SystemConfigConst.BACKUP_DAY_OF_WEEK_DEFAULT), 1);
    }

    public Integer getDayOfMonth() {
        return parseInt(get(SystemConfigConst.BACKUP_DAY_OF_MONTH, SystemConfigConst.BACKUP_DAY_OF_MONTH_DEFAULT), 1);
    }

    /** 给 SQLBackUpTask（Phase 4）现读 cron */
    public String getCron() {
        return CronBuilder.build(getFrequency(), getTime(), getDayOfWeek(), getDayOfMonth());
    }

    // ── helpers ────────────────────────────────────────────

    private String get(String key, String defVal) {
        String v = appConfigService.getValue(SystemConfigConst.DOMAIN_BACKUP, key);
        return v == null ? defVal : v;
    }

    private void set(String key, String val) {
        appConfigService.setValue(SystemConfigConst.DOMAIN_BACKUP, key, val);
    }

    private static boolean parseBool(String v) {
        return "true".equalsIgnoreCase(v);
    }

    private static int parseInt(String v, int def) {
        try { return Integer.parseInt(v); } catch (Exception e) { return def; }
    }
}
