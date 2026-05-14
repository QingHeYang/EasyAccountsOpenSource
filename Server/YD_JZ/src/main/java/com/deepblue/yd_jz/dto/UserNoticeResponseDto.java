package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.UserNotice;
import lombok.Data;

import java.text.SimpleDateFormat;
import java.util.Date;

// v2.7.0: 用户通知响应
@Data
public class UserNoticeResponseDto {

    private Integer id;
    private Integer type;
    private String title;
    private String content;
    private Integer relatedRuleId;
    private String relatedRunDate;
    private boolean read;
    private String createTime;

    public static UserNoticeResponseDto fromEntity(UserNotice e) {
        if (e == null) return null;
        UserNoticeResponseDto d = new UserNoticeResponseDto();
        d.setId(e.getId());
        d.setType(e.getType());
        d.setTitle(e.getTitle());
        d.setContent(e.getContent());
        d.setRelatedRuleId(e.getRelatedRuleId());
        d.setRelatedRunDate(formatDate(e.getRelatedRunDate()));
        d.setRead(e.isRead());
        d.setCreateTime(formatDateTime(e.getCreateTime()));
        return d;
    }

    private static String formatDate(Date date) {
        return date == null ? null : new SimpleDateFormat("yyyy-MM-dd").format(date);
    }

    private static String formatDateTime(Date date) {
        return date == null ? null : new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }
}
