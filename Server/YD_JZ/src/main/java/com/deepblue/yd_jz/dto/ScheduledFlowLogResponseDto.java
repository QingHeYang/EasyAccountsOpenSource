package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.ScheduledFlowLog;
import lombok.Data;

import java.text.SimpleDateFormat;
import java.util.Date;

// v2.7.0: 执行日志响应
@Data
public class ScheduledFlowLogResponseDto {

    private Integer id;
    private Integer ruleId;
    private String ruleName;       // 冗余展示
    private String executeTime;
    private boolean success;
    private Integer flowId;
    private Integer failCategory;  // 1=主数据类 2=其他类；成功为 null
    private String failReason;

    public static ScheduledFlowLogResponseDto fromEntity(ScheduledFlowLog e) {
        if (e == null) return null;
        ScheduledFlowLogResponseDto d = new ScheduledFlowLogResponseDto();
        d.setId(e.getId());
        d.setRuleId(e.getRuleId());
        d.setExecuteTime(formatDateTime(e.getExecuteTime()));
        d.setSuccess(e.isSuccess());
        d.setFlowId(e.getFlowId());
        d.setFailCategory(e.getFailCategory());
        d.setFailReason(e.getFailReason());
        if (e.getRule() != null) d.setRuleName(e.getRule().getName());
        return d;
    }

    private static String formatDateTime(Date date) {
        return date == null ? null : new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }
}
