package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.*;
import com.deepblue.yd_jz.service.ExcelService;
import com.deepblue.yd_jz.service.FlowService;
import com.deepblue.yd_jz.data.MonthExcelData;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/flow")
@Api(value = "FlowController", tags = {"流水管理"})
public class FlowController {

    @Autowired
    FlowService flowService;

    @Autowired
    ExcelService excelService;

    @ApiOperation(value = "添加流水")
    @PostMapping("/addFlow")
    public BaseDto addFlow(@RequestBody FlowAddRequestDto flowAddRequestDto) throws Exception {
        flowService.doAddFlow(flowAddRequestDto);
        return BaseDto.setSuccessBean();
    }


    @ApiOperation(value = "获取指定一笔流水")
    @GetMapping("/getFlow/{id}")
    public BaseDto<FlowSingleResponseDto> getFlowById(@PathVariable int id) {
        FlowSingleResponseDto flowSingleResponseDto = flowService.doQueryFlow(id);
        BaseDto<FlowSingleResponseDto> baseDto = BaseDto.setSuccessBean();
        if (flowSingleResponseDto == null) {
            baseDto.setCode(403);
            baseDto.setMsg("未查询到该条记录");
        } else {
            baseDto.setData(flowSingleResponseDto);
        }
        return baseDto;
    }

    @ApiOperation(value = "更新流水")
    @PutMapping("/updateFlow/{id}")
    public BaseDto updateFlow(@PathVariable int id, @RequestBody FlowAddRequestDto flowAddRequestDto) throws Exception {
        flowService.doUpdateFlow(id, flowAddRequestDto);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "收藏流水")
    @PutMapping("/collectFlow/{id}/{collect}")
    public BaseDto updateFlow(@PathVariable int id, @PathVariable int collect) throws Exception {
        flowService.doUpdateFlowCollect(id,collect);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "删除流水")
    @DeleteMapping("/deleteFlow/{id}")
    public BaseDto deleteFlow(@PathVariable int id) throws Exception {
        flowService.doDeleteFlow(id);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "获取主业流水")
    @ApiParam(name = "chooseHandle", value = "0:全部 1:支出 2:收入", required = true)
    @GetMapping("/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}")
    public BaseDto<FlowListDto> getFlowListMain(@PathVariable int chooseHandle, @PathVariable int chooseOrder
            , @PathVariable String date ){
        FlowListDto flowListDto = flowService.doGetMainBean(chooseHandle,chooseOrder,date);
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(flowListDto);
        return baseDto;
    }

    @ApiOperation(value = "月度流水Excel")
    @GetMapping("/makeExcel/{date}")
    public BaseDto<ExcelDto> getExcel(@PathVariable String date){
        String  result =excelService.makeMonthExcel(date);
        ExcelDto excelDto = new ExcelDto();
        String flag = result.substring(result.length()-2);
        String log = result.substring(0,result.length()-2);
        excelDto.setLog(log);
        excelDto.setSuccess(flag.contains("0"));
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(excelDto);
        return baseDto;
    }
}
