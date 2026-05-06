package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import lombok.Data;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Date;

// v2.7.0: 定时记账规则 创建/修改 入参
@Data
public class ScheduledFlowRuleRequestDto {

    private String name;
    private String money;

    private Integer typeId;
    private Integer actionId;
    private Integer accountId;
    private Integer accountToId;

    private String note;

    // 1=每日 2=每周 3=每月 4=每年
    private Integer cycleType;
    // JSON 字符串：每日 null；每周 [1-7]；每月 [1-31]；每年 ["MM-DD"]
    private String cycleDates;
    // HH:mm 或 HH:mm:ss
    private String runTime;

    // yyyy-MM-dd
    private String startDate;
    // yyyy-MM-dd，选填
    private String endDate;

    private Boolean reminderEnabled;
    private Boolean emailEnabled;

    /**
     * 转成 Entity；字段合法性的业务校验在 Service 层做
     */
    public ScheduledFlowRule toEntity() {
        ScheduledFlowRule e = new ScheduledFlowRule();
        e.setName(name);
        e.setMoney(money);
        e.setTypeId(typeId);
        e.setActionId(actionId);
        e.setAccountId(accountId);
        // 0 视为未填，避免前端传默认值 0
        e.setAccountToId(accountToId == null || accountToId == 0 ? null : accountToId);
        e.setNote(note);
        e.setCycleType(cycleType);
        e.setCycleDates(cycleDates);
        e.setRunTime(runTime);
        e.setStartDate(parseDate(startDate));
        e.setEndDate(parseDate(endDate));
        e.setReminderEnabled(Boolean.TRUE.equals(reminderEnabled));
        e.setEmailEnabled(Boolean.TRUE.equals(emailEnabled));
        return e;
    }

    private static Date parseDate(String s) {
        if (s == null || s.trim().isEmpty()) return null;
        return Date.from(LocalDate.parse(s.trim())
                .atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
