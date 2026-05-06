package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import lombok.Data;

import java.text.SimpleDateFormat;
import java.util.Date;

// v2.7.0: 定时记账规则 列表/详情 响应
@Data
public class ScheduledFlowRuleResponseDto {

    private Integer id;
    private String name;
    private String money;

    private Integer typeId;
    private String typeName;
    private Integer actionId;
    private String actionName;
    private Integer accountId;
    private String accountName;
    private Integer accountToId;
    private String accountToName;

    private String note;

    private Integer cycleType;
    private String cycleDates;
    private String runTime;

    private String startDate;
    private String endDate;
    private boolean permanent;

    private Integer status;
    private String nextRunDate;
    private String lastRunDate;

    private boolean reminderEnabled;
    private boolean emailEnabled;

    private String createTime;

    public static ScheduledFlowRuleResponseDto fromEntity(ScheduledFlowRule e) {
        if (e == null) return null;
        ScheduledFlowRuleResponseDto d = new ScheduledFlowRuleResponseDto();
        d.setId(e.getId());
        d.setName(e.getName());
        d.setMoney(e.getMoney());
        d.setTypeId(e.getTypeId());
        d.setActionId(e.getActionId());
        d.setAccountId(e.getAccountId());
        d.setAccountToId(e.getAccountToId());
        d.setNote(e.getNote());
        d.setCycleType(e.getCycleType());
        d.setCycleDates(e.getCycleDates());
        d.setRunTime(e.getRunTime());
        d.setStartDate(formatDate(e.getStartDate()));
        d.setEndDate(formatDate(e.getEndDate()));
        d.setPermanent(e.isPermanent());
        d.setStatus(e.getStatus());
        d.setNextRunDate(formatDate(e.getNextRunDate()));
        d.setLastRunDate(formatDate(e.getLastRunDate()));
        d.setReminderEnabled(e.isReminderEnabled());
        d.setEmailEnabled(e.isEmailEnabled());
        d.setCreateTime(formatDateTime(e.getCreateTime()));

        // 关联展开
        if (e.getAccount() != null) d.setAccountName(e.getAccount().getAName());
        if (e.getAccountTo() != null) d.setAccountToName(e.getAccountTo().getAName());
        if (e.getAction() != null) d.setActionName(e.getAction().getHName());
        if (e.getType() != null) d.setTypeName(e.getType().getTName());

        return d;
    }

    private static String formatDate(Date date) {
        return date == null ? null : new SimpleDateFormat("yyyy-MM-dd").format(date);
    }

    private static String formatDateTime(Date date) {
        return date == null ? null : new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }
}
