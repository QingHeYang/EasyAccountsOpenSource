package com.deepblue.yd_jz.dto;

import lombok.Data;
import java.util.List;

/**
 * 公告通知 DTO
 */
@Data
public class NoticeDto {
    private List<Notice> notices;

    @Data
    public static class Notice {
        private Integer id;
        private String title;
        private String content;
        private String date;
        private String url;
        private String expire;
    }
}
