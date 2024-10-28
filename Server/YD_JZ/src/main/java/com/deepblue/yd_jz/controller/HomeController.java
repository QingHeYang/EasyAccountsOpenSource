package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.HomeDto;
import com.deepblue.yd_jz.service.HomeService;
import com.deepblue.yd_jz.service.ScreenService;
import com.deepblue.yd_jz.dto.BaseDto;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@Api(value = "HomeController", tags = {"首页信息"})
@RequestMapping("/home")
public class HomeController {
    @Autowired
    HomeService homeService;

    @Autowired
    ScreenService screenService;

    @Value("${webhook_url}")
    private String webhookUrl;

    @ApiOperation(value = "获取首页信息")
    @GetMapping("/getHomeInfo")
    public BaseDto<HomeDto> getHomeInfo() {
        HomeDto homeDto = homeService.getHomeBean();
        BaseDto baseDto = new BaseDto();
        baseDto.setData(homeDto);
        return baseDto;
    }
}
