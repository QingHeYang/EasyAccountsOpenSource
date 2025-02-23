package com.deepblue.yd_jz.controller;

import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.alibaba.dashscope.exception.UploadFileException;
import com.deepblue.yd_jz.dto.*;
import com.deepblue.yd_jz.service.AIAnalysisService;
import com.deepblue.yd_jz.service.ExcelService;
import com.deepblue.yd_jz.service.FlowService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Random;

@RestController
@RequestMapping("/flow")
@Api(value = "FlowController", tags = {"流水管理"})
public class FlowController {

    @Autowired
    FlowService flowService;

    @Autowired
    ExcelService excelService;

    @Autowired
    AIAnalysisService aiAnalyzeService;

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

    @ApiOperation(value = "Ai分析截图账单")
    @PostMapping("/analyzeFlowByAi")
    public BaseDto analyzeFlowByAi(@RequestParam("file") MultipartFile file){
        // 从网页获取到图片文件后，存入当前工程的 /static/pic
        String currentDir = System.getProperty("user.dir");
        Path path = Paths.get(currentDir, "YD_JZ/src/main/resources/static/pic");
        try {
            if (!Files.exists(path)) {
                Files.createDirectories(path);
            }

            // 下面这段逻辑是：图片重命名，避免文件冲突
            // 获取当前日期并格式化为 "yyyyMMdd"
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMddHHmm");
            String date = sdf.format(new Date());
            // 生成 6 位随机数
            Random random = new Random();
            int randomNumber = 100000 + random.nextInt(900000);
            String originalFilename = file.getOriginalFilename();
            // 获取原始文件名和其扩展名
            String extension = "";
            int dotIndex = originalFilename.lastIndexOf('.');
            if (dotIndex > 0 && dotIndex < originalFilename.length() - 1) {
                extension = originalFilename.substring(dotIndex);
            }
            // 去掉原始文件名中的扩展名部分
            String baseName = originalFilename.substring(0, dotIndex);
            // 为避免文件重名，按：IMG_20250215_784609.jpg 格式存储
            String newFilename = baseName + "_" + date + "_" + randomNumber + extension;
            String filePath = path + "/" + newFilename;
            File destFile = new File(filePath);
            file.transferTo(destFile);

            // 调用AI服务
            List<FlowAddRequestDto> flowAddRequestDtoList = aiAnalyzeService.analyzeFlowByAi(filePath);

            // 获取到一组Gson解析好的对象，挨个调用addFlow服务
            for (FlowAddRequestDto flowAddRequestDto : flowAddRequestDtoList) {
                System.out.println("开始添加每一条流水");
                System.out.println(flowAddRequestDto);

                flowService.doAddFlow(flowAddRequestDto);

                System.out.println("本条流水添加成功！！");
            }

        }catch (Exception e) {
            throw new RuntimeException(e);
        }

        BaseDto baseDto = BaseDto.setSuccessBean();
        return baseDto;
    }
}
