package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.data.AnalysisExcelData;
import com.deepblue.yd_jz.dto.AnalysisResponseDto;
import com.deepblue.yd_jz.dto.AnalysisTypeListRequestDto;
import com.deepblue.yd_jz.dto.AnalysisTypeRequestDto;
import com.deepblue.yd_jz.service.AnalysisService;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.data.MonthExcelData;
import com.deepblue.yd_jz.service.AnalysisV2Service;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/analysis")
@Api(value = "AnalysisController", tags = {"财务分析"})
public class AnalysisController {
    @Autowired
    AnalysisService analysisService;

    @Autowired
    AnalysisV2Service analysisV2Service;

    @ApiOperation(value = "财务分析")
    @GetMapping("/doAnalysis")
    public BaseDto<AnalysisResponseDto> doAnalysis(@RequestParam("start") String start, @RequestParam(value = "end", required = false) String end) {
        BaseDto baseDto = BaseDto.setSuccessBean();
        AnalysisResponseDto analysisResponseDto =analysisService.doAnalysis(start, end);
        baseDto.setData(analysisResponseDto);
        return baseDto;
    }

    @ApiOperation(value = "导出Excel")
    @GetMapping("/exportExcel")
    public BaseDto<MonthExcelData> exportExcel(@RequestParam("start") String start, @RequestParam(value = "end", required = false) String end) {
        AnalysisExcelData excelBean = analysisService.doMakeAnalysisExcel(start, end);
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(excelBean);
        return baseDto;
    }

    @ApiOperation(value = "获取时间内收支分类列表")
    @PostMapping("/v2/getAnalysisTypeList")
    public BaseDto getAnalysisTypeList(@RequestBody AnalysisTypeListRequestDto analysisTypeListRequestDto) {
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(analysisV2Service.getAnalysisTypeList(analysisTypeListRequestDto));
        return baseDto;
    }

    @ApiOperation(value = "获取时间内收支分类每月数据")
    @PostMapping("/v2/getAnalysisTypeMonthData")
    public BaseDto getAnalysisTypeMonthData(@RequestBody AnalysisTypeRequestDto typeRequestDto) {
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(analysisV2Service.getAnalysisTypeMonthData(typeRequestDto));
        return baseDto;
    }
}
