package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.FlowListDto;
import com.deepblue.yd_jz.dto.ScreenFlowRequestDto;
import com.deepblue.yd_jz.service.ScreenService;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.utils.LogUtils;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/screen")
@Api(value ="ScreenController",tags = {"筛选功能"})
public class ScreenController {
    @Autowired
    ScreenService screenService;

    @ApiOperation(value = "获取筛选功能")
    @PostMapping("/getFlowByScreen")
    public BaseDto<FlowListDto> getFlowByScreen(@RequestBody ScreenFlowRequestDto screenFlowRequestDto) {
        LogUtils.log_json(screenFlowRequestDto);
       FlowListDto flowListDto =  screenService.getFlowByScreen(screenFlowRequestDto);
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(flowListDto);
        return baseDto;
    }

    @Deprecated
    @PostMapping("/makeScreenExcel")
    public BaseDto makeScreenExcel(@RequestBody ScreenFlowRequestDto screenFlowRequestDto) {
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "生成Excel")
    @PostMapping("/makeExcel")
    public BaseDto makeScreenExcel(@RequestBody ScreenFlowRequestDto screenFlowRequestDto, @RequestParam String excelName) throws Exception {
        screenService.makeScreenExcel(screenFlowRequestDto,excelName);
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(excelName);
        return baseDto;
    }
}
