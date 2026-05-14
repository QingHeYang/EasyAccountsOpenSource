package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.AppConfigRepository;
import com.deepblue.yd_jz.entity.AppConfig;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

// v2.7.0: 全局应用配置 k-v 读写
@Slf4j
@Service
public class AppConfigService {

    private static final Pattern HHMM = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d$");

    @Autowired
    private AppConfigRepository repo;

    // ────────────── 通用 k-v 读写 ──────────────

    public String getValue(String domain, String key) {
        AppConfig c = repo.findByDomainAndConfigKey(domain, key);
        return c == null ? null : c.getConfigValue();
    }

    @Transactional(rollbackFor = Exception.class)
    public void setValue(String domain, String key, String value) {
        AppConfig c = repo.findByDomainAndConfigKey(domain, key);
        if (c == null) {
            c = new AppConfig();
            c.setDomain(domain);
            c.setConfigKey(key);
        }
        c.setConfigValue(value);
        c.setUpdatedAt(new Date());
        repo.save(c);
    }

    /**
     * 读取整个 domain 下的 k-v 集合
     */
    public Map<String, String> getDomainMap(String domain) {
        List<AppConfig> list = repo.findByDomain(domain);
        Map<String, String> map = new HashMap<>();
        for (AppConfig c : list) {
            map.put(c.getConfigKey(), c.getConfigValue());
        }
        return map;
    }

    // ────────────── 定时记账提醒配置（语义方法）──────────────

    /**
     * 读：提醒前 N 天（1~5）
     */
    public int getRemindBeforeDays() {
        String v = getValue(ScheduledFlowConst.CONFIG_DOMAIN_SCHEDULED_FLOW,
                ScheduledFlowConst.CONFIG_KEY_REMIND_BEFORE_DAYS);
        try {
            return v == null ? 1 : Integer.parseInt(v);
        } catch (NumberFormatException e) {
            return 1;
        }
    }

    /**
     * 读：全局提醒时间 HH:mm
     */
    public String getRemindTime() {
        String v = getValue(ScheduledFlowConst.CONFIG_DOMAIN_SCHEDULED_FLOW,
                ScheduledFlowConst.CONFIG_KEY_REMIND_TIME);
        return v == null ? "09:00" : v;
    }

    /**
     * 更新定时记账全局提醒配置
     */
    @Transactional(rollbackFor = Exception.class)
    public void updateReminderConfig(int remindBeforeDays, String remindTime) {
        if (remindBeforeDays < 1 || remindBeforeDays > 5) {
            throw new BusinessException(ErrorCode.PARAM_INVALID, "提醒前 N 天必须在 1~5 之间");
        }
        if (remindTime == null || !HHMM.matcher(remindTime.trim()).matches()) {
            throw new BusinessException(ErrorCode.PARAM_FORMAT_ERROR, "提醒时间格式错误，应为 HH:mm");
        }
        setValue(ScheduledFlowConst.CONFIG_DOMAIN_SCHEDULED_FLOW,
                ScheduledFlowConst.CONFIG_KEY_REMIND_BEFORE_DAYS,
                String.valueOf(remindBeforeDays));
        setValue(ScheduledFlowConst.CONFIG_DOMAIN_SCHEDULED_FLOW,
                ScheduledFlowConst.CONFIG_KEY_REMIND_TIME,
                remindTime.trim());
    }
}
