package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.NoticeDto;
import com.google.gson.Gson;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 公告通知服务
 * 用户主动调用获取公告列表
 */
@Slf4j
@Service
public class NoticeService {

    @Value("${notices.url:}")
    private String noticesUrl;

    private static final Gson GSON = new Gson();
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /**
     * 获取公告列表（过滤掉已过期的）
     * @return 未过期的公告列表
     */
    public List<NoticeDto.Notice> getNotices() {
        if (noticesUrl == null || noticesUrl.trim().isEmpty()) {
            log.debug("未配置公告地址");
            return new ArrayList<>();
        }

        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(noticesUrl))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();

            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                NoticeDto noticeDto = GSON.fromJson(response.body(), NoticeDto.class);

                if (noticeDto == null || noticeDto.getNotices() == null) {
                    return new ArrayList<>();
                }

                // 过滤掉已过期的公告
                LocalDate today = LocalDate.now();
                return noticeDto.getNotices().stream()
                        .filter(notice -> !isExpired(notice, today))
                        .collect(Collectors.toList());
            } else {
                log.warn("获取公告失败，状态码: {}", response.statusCode());
            }
        } catch (Exception e) {
            log.warn("获取公告失败: {}", e.getMessage());
        }

        return new ArrayList<>();
    }

    /**
     * 判断公告是否已过期
     */
    private boolean isExpired(NoticeDto.Notice notice, LocalDate today) {
        if (notice.getExpire() == null || notice.getExpire().trim().isEmpty()) {
            return false;  // 无过期日期，永不过期
        }

        try {
            LocalDate expireDate = LocalDate.parse(notice.getExpire(), DATE_FORMATTER);
            return today.isAfter(expireDate);
        } catch (Exception e) {
            log.warn("解析过期日期失败: {}", notice.getExpire());
            return false;  // 解析失败，不过期
        }
    }
}
