package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.dto.UserNoticeResponseDto;
import com.deepblue.yd_jz.service.UserNoticeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

// v2.7.0: 用户信息通知（本地生成）REST API
// 与现有 /home/getNotices（云端公告）是两个独立概念
@Slf4j
@RestController
@Tag(name = "信息通知")
@RequestMapping("/notice")
public class NoticeController {

    @Autowired
    private UserNoticeService noticeService;

    @Operation(summary = "通知列表，isRead 可选 true/false")
    @GetMapping("/list")
    public BaseDto<List<UserNoticeResponseDto>> list(@RequestParam(required = false) Boolean isRead) {
        List<UserNoticeResponseDto> list = (isRead == null
                ? noticeService.listAll()
                : noticeService.listByRead(isRead)).stream()
                .map(UserNoticeResponseDto::fromEntity)
                .collect(Collectors.toList());
        BaseDto<List<UserNoticeResponseDto>> res = BaseDto.setSuccessBean();
        res.setData(list);
        return res;
    }

    @Operation(summary = "单条标记已读")
    @PutMapping("/{id}/read")
    public BaseDto markRead(@PathVariable Integer id) {
        noticeService.markRead(id);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "全部标记已读")
    @PutMapping("/markAllRead")
    public BaseDto markAllRead() {
        noticeService.markAllRead();
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "删除单条通知")
    @DeleteMapping("/{id}")
    public BaseDto delete(@PathVariable Integer id) {
        noticeService.delete(id);
        return BaseDto.setSuccessBean();
    }
}
