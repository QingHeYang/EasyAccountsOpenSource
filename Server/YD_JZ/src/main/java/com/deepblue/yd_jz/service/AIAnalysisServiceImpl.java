package com.deepblue.yd_jz.service;

import com.alibaba.dashscope.aigc.generation.GenerationResult;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.alibaba.dashscope.exception.UploadFileException;
import com.deepblue.yd_jz.dto.AccountResponseDto;
import com.deepblue.yd_jz.dto.FlowAddRequestDto;
import com.deepblue.yd_jz.dto.TypeListResponseDto;
import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.QwenBean;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.lang.reflect.Type;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * AI 分析服务实现
 * @author rockyshen
 * @date 2025/2/23 15:21
 */
@Slf4j
@Service
public class AIAnalysisServiceImpl implements AIAnalysisService {

    private static final Gson GSON = new Gson();
    @Autowired
    private QwenBean qwenBean;

    @Autowired
    private AccountService accountService;

    @Autowired
    private ActionService actionService;

    @Autowired
    private TypeService typeService;

    /**
     * 调用AI大模型，提供自动记账能力
     * controller接受支付宝、微信等账单截图，调用阿里通义千问大模型，分析账单，自动封装成flowAddRequest实体类，生成Flow
     * @param filePath 图片文件路径
     * @return 解析出的流水列表
     */
    @Override
    public List<FlowAddRequestDto> analyzeFlowByAi(String filePath) throws NoApiKeyException, UploadFileException, InputRequiredException {
        // 1. OCR 识别图片文字
        log.info("开始 OCR 识别: {}", filePath);
        String flowInfo = qwenBean.ocrConversationCall(filePath);
        if (flowInfo == null || flowInfo.trim().isEmpty()) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "OCR识别失败，未能提取图片文字");
        }
        log.debug("OCR 识别结果: {}", flowInfo);

        // 2. 构建 Action 映射 (ID -> 名称)
        List<Action> actions = actionService.getActions();
        String actionMapString = actions.stream()
                .map(action -> "ID: " + action.getId() + ", Action名: " + action.getHName())
                .collect(Collectors.joining(";"));

        // 3. 构建 Type 映射 (过滤停用分类)
        List<TypeListResponseDto> typeList = typeService.queryAllType(false);
        String typeMapString = typeList.stream()
                .filter(type -> type.getTName() != null && !type.getTName().contains("停用"))
                .map(type -> "ID: " + type.getId() + ", Type名: " + type.getTName())
                .collect(Collectors.joining(";"));

        // 4. 获取默认账户
        List<AccountResponseDto> allAccount = accountService.getAllAccount();
        List<AccountResponseDto> defaultAccounts = allAccount.stream()
                .filter(account -> account.getNote() != null && account.getNote().contains("默认"))
                .collect(Collectors.toList());

        if (defaultAccounts.isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_ERROR, "请在账户备注中包含'默认'以指定AI记账的默认账户");
        }

        // 随机选择一个默认账户
        int randomIndex = ThreadLocalRandom.current().nextInt(defaultAccounts.size());
        int defaultAccountId = defaultAccounts.get(randomIndex).getId();

        // 5. 调用 AI 解析账单
        log.info("调用 AI 解析账单，默认账户ID: {}", defaultAccountId);
        GenerationResult result = qwenBean.callWithMessage(flowInfo, actionMapString, typeMapString, defaultAccountId);

        // 6. 解析 AI 返回结果
        String content = result.getOutput().getChoices().get(0).getMessage().getContent();
        log.debug("AI 返回内容: {}", content);

        String json = extractJson(content);
        if (json == null || json.trim().isEmpty()) {
            log.warn("AI 未返回有效的 JSON 数据");
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "AI未能识别账单信息，请确保图片清晰且为账单截图");
        }

        // 7. JSON 解析为对象列表
        try {
            Type listType = new TypeToken<List<FlowAddRequestDto>>(){}.getType();
            List<FlowAddRequestDto> flowList = GSON.fromJson(json, listType);
            log.info("AI 解析成功，识别出 {} 条流水", flowList != null ? flowList.size() : 0);
            return flowList != null ? flowList : Collections.emptyList();
        } catch (JsonSyntaxException e) {
            log.error("JSON 解析失败: {}", json, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "AI返回数据格式错误，无法解析");
        }
    }

    public String extractJson(String input) {
        // 定义匹配 JSON 数组的正则表达式
        String jsonArrayPattern = "\\[\\s*\\{.*?\\}\\s*\\]";

        // 编译正则表达式
        Pattern pattern = Pattern.compile(jsonArrayPattern, Pattern.DOTALL);
        Matcher matcher = pattern.matcher(input);

        // 寻找匹配部分并返回
        if (matcher.find()) {
            return matcher.group();
        } else {
            return null; // 如果没有找到 JSON，则返回 null 或其他提示信息
        }
    }

}
