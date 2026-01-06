package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.*;
import com.deepblue.yd_jz.service.AIAnalysisService;
import com.deepblue.yd_jz.service.ExcelService;
import com.deepblue.yd_jz.service.FlowService;
import com.deepblue.yd_jz.data.MonthExcelData;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Random;

@RestController
@RequestMapping("/flow")
@Tag(name = "流水管理")
public class FlowController {

    @Autowired
    FlowService flowService;

    @Autowired
    ExcelService excelService;

    @Autowired
    AIAnalysisService aiAnalyzeService;

    @Operation(summary = "添加流水")
    @PostMapping("/addFlow")
    public BaseDto<FlowIdResponseDto> addFlow(@RequestBody FlowAddRequestDto flowAddRequestDto) throws Exception {
        int id = flowService.doAddFlow(flowAddRequestDto);
        BaseDto<FlowIdResponseDto> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(new FlowIdResponseDto(id));
        return baseDto;
    }


    @Operation(summary = "获取指定一笔流水")
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

    @Operation(summary = "更新流水")
    @PutMapping("/updateFlow/{id}")
    public BaseDto<FlowIdResponseDto> updateFlow(@PathVariable int id, @RequestBody FlowAddRequestDto flowAddRequestDto) throws Exception {
        int flowId = flowService.doUpdateFlow(id, flowAddRequestDto);
        BaseDto<FlowIdResponseDto> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(new FlowIdResponseDto(flowId));
        return baseDto;
    }

    @Operation(summary = "收藏流水")
    @PutMapping("/collectFlow/{id}/{collect}")
    public BaseDto updateFlow(@PathVariable int id, @PathVariable int collect) throws Exception {
        flowService.doUpdateFlowCollect(id,collect);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "删除流水")
    @DeleteMapping("/deleteFlow/{id}")
    public BaseDto deleteFlow(@PathVariable int id) throws Exception {
        flowService.doDeleteFlow(id);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "获取主业流水")
    @Parameter(name = "chooseHandle", description = "0:全部 1:支出 2:收入", required = true)
    @GetMapping("/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}")
    public BaseDto<FlowListDto> getFlowListMain(@PathVariable int chooseHandle, @PathVariable int chooseOrder
            , @PathVariable String date ){
        FlowListDto flowListDto = flowService.doGetMainBean(chooseHandle,chooseOrder,date);
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(flowListDto);
        return baseDto;
    }

    @Operation(summary = "月度流水Excel")
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

    /**
     * AI 分析截图账单 (PR #3 by rockyshen)
     * 上传账单图片，通过阿里通义千问 OCR 识别后自动生成流水
     */
    @Operation(summary = "AI分析截图账单")
    @PostMapping("/analyzeFlowByAi")
    public BaseDto analyzeFlowByAi(@RequestParam("file") MultipartFile file){
        // 从网页获取到图片文件后，存入当前工程的 /static/pic
        String currentDir = System.getProperty("user.dir");
        Path path = Paths.get(currentDir, "YD_JZ/src/main/resources/static/pic");
        try {
            if (!Files.exists(path)) {
                Files.createDirectories(path);
            }

            // 图片重命名，避免文件冲突
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMddHHmm");
            String date = sdf.format(new Date());
            Random random = new Random();
            int randomNumber = 100000 + random.nextInt(900000);
            String originalFilename = file.getOriginalFilename();
            String extension = "";
            int dotIndex = originalFilename.lastIndexOf('.');
            if (dotIndex > 0 && dotIndex < originalFilename.length() - 1) {
                extension = originalFilename.substring(dotIndex);
            }
            String baseName = originalFilename.substring(0, dotIndex);
            String newFilename = baseName + "_" + date + "_" + randomNumber + extension;
            String filePath = path + "/" + newFilename;
            File destFile = new File(filePath);
            file.transferTo(destFile);

            // 调用AI服务
            List<FlowAddRequestDto> flowAddRequestDtoList = aiAnalyzeService.analyzeFlowByAi(filePath);

            // 获取到一组解析好的对象，挨个调用addFlow服务
            for (FlowAddRequestDto flowAddRequestDto : flowAddRequestDtoList) {
                flowService.doAddFlow(flowAddRequestDto);
            }

        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        BaseDto baseDto = BaseDto.setSuccessBean();
        return baseDto;
    }
}
