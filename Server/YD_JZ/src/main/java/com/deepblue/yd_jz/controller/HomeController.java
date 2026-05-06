package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.HomeDto;
import com.deepblue.yd_jz.dto.NoticeDto;
import com.deepblue.yd_jz.dto.VersionDto;
import com.deepblue.yd_jz.service.HomeService;
import com.deepblue.yd_jz.service.NoticeService;
import com.deepblue.yd_jz.service.ScreenService;
import com.deepblue.yd_jz.dto.BaseDto;

import java.util.List;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@Tag(name = "首页信息")
@RequestMapping("/home")
public class HomeController {
    @Autowired
    HomeService homeService;

    @Autowired
    ScreenService screenService;

    @Autowired
    NoticeService noticeService;

    @Operation(summary = "获取首页信息")
    @GetMapping("/getHomeInfo")
    public BaseDto<HomeDto> getHomeInfo() {
        HomeDto homeDto = homeService.getHomeBean();
        BaseDto baseDto = new BaseDto();
        baseDto.setData(homeDto);
        return baseDto;
    }

    @Operation(summary = "V2版本获取首页信息")
    @GetMapping("/getHomeInfoV2/{year}")
    public BaseDto<HomeDto> getHomeInfoV2(@PathVariable int year) {
        HomeDto homeDto = homeService.getHomeInfoByTime(year);
        BaseDto baseDto = new BaseDto();
        baseDto.setData(homeDto);
        return baseDto;
    }

    @Operation(summary = "获取版本信息")
    @GetMapping("/getVersion")
    public BaseDto<VersionDto> getVersion() {
        BaseDto baseDto = new BaseDto();
        baseDto.setData(homeService.getVersion());
        return baseDto;
    }

    @Operation(summary = "获取公告列表")
    @GetMapping("/getNotices")
    public BaseDto<List<NoticeDto.Notice>> getNotices() {
        BaseDto baseDto = new BaseDto();
        baseDto.setData(noticeService.getNotices());
        return baseDto;
    }
}
