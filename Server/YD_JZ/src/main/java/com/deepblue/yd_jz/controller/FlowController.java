package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.*;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.service.AIAnalysisService;
import com.deepblue.yd_jz.service.ExcelService;
import com.deepblue.yd_jz.service.FlowService;
import com.deepblue.yd_jz.data.MonthExcelData;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

@Slf4j
@RestController
@RequestMapping("/flow")
@Tag(name = "流水管理")
public class FlowController {

    /** 允许的图片类型 */
    private static final Set<String> ALLOWED_EXTENSIONS = Set.of(".jpg", ".jpeg", ".png", ".gif", ".webp");
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    @Autowired
    FlowService flowService;

    @Autowired
    ExcelService excelService;

    @Autowired
    AIAnalysisService aiAnalyzeService;

    @Value("${image.upload.path:/Ledger/images/}")
    private String imageUploadPath;

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
    public BaseDto<Integer> analyzeFlowByAi(@RequestParam("file") MultipartFile file) {
        // 1. 文件校验
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || originalFilename.isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_ERROR, "文件名不能为空");
        }
        if (file.isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_ERROR, "文件内容为空");
        }

        // 2. 扩展名校验
        String extension = "";
        int dotIndex = originalFilename.lastIndexOf('.');
        if (dotIndex > 0) {
            extension = originalFilename.substring(dotIndex).toLowerCase();
        }
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            throw new BusinessException(ErrorCode.PARAM_ERROR,
                "不支持的文件类型，仅支持: " + String.join(", ", ALLOWED_EXTENSIONS));
        }

        // 3. 保存图片到配置的上传目录
        String filePath;
        try {
            Path uploadDir = Paths.get(imageUploadPath, "ai");
            if (!Files.exists(uploadDir)) {
                Files.createDirectories(uploadDir);
            }

            // 生成唯一文件名: ai_20260106143022_123456.jpg
            String timestamp = LocalDateTime.now().format(DATE_FORMATTER);
            int randomNumber = ThreadLocalRandom.current().nextInt(100000, 999999);
            String newFilename = "ai_" + timestamp + "_" + randomNumber + extension;
            filePath = uploadDir.resolve(newFilename).toString();

            File destFile = new File(filePath);
            file.transferTo(destFile);
            log.info("AI账单图片已保存: {}", filePath);

        } catch (IOException e) {
            log.error("图片保存失败", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "图片保存失败: " + e.getMessage());
        }

        // 4. 调用 AI 服务分析
        List<FlowAddRequestDto> flowList;
        try {
            flowList = aiAnalyzeService.analyzeFlowByAi(filePath);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI分析失败", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "AI分析失败: " + e.getMessage());
        }

        // 5. 批量添加流水
        if (flowList == null || flowList.isEmpty()) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "AI未能识别出账单信息");
        }

        int successCount = 0;
        for (FlowAddRequestDto flowAddRequestDto : flowList) {
            try {
                flowService.doAddFlow(flowAddRequestDto);
                successCount++;
            } catch (Exception e) {
                log.warn("添加流水失败: {}", flowAddRequestDto.getNote(), e);
            }
        }

        log.info("AI账单分析完成，识别 {} 条，成功添加 {} 条", flowList.size(), successCount);

        BaseDto<Integer> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(successCount);
        return baseDto;
    }
}
