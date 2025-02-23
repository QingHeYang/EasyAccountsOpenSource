package com.deepblue.yd_jz.service;

import com.alibaba.dashscope.aigc.generation.GenerationResult;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.alibaba.dashscope.exception.UploadFileException;
import com.deepblue.yd_jz.dto.AccountResponseDto;
import com.deepblue.yd_jz.dto.FlowAddRequestDto;
import com.deepblue.yd_jz.dto.TypeListResponseDto;
import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.utils.QwenBean;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.lang.reflect.Type;
import java.util.List;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * @author rockyshen
 * @date 2025/2/23 15:21
 */
@Service
public class AIAnalysisServiceImpl implements AIAnalysisService {
    @Autowired
    private QwenBean qwenBean;

    @Autowired
    private AccountService accountService;

    @Autowired
    private ActionService actionService;

    @Autowired
    private TypeService typeService;

    /** 调用AI大模型，提供自动记账能力
     * controller接受支付宝、微信等账单截图，调用阿里通义千问大模型，分析账单，自动封装成flowAddRequest实体类，生成Flow
     * @param filePath
     */
    @Override
    public List<FlowAddRequestDto> analyzeFlowByAi(String filePath) throws NoApiKeyException, UploadFileException, InputRequiredException {
        String flowInfo = null;
        flowInfo = qwenBean.ocrConversationCall(filePath);

        // 还要传action与id的映射关系，type与id的映射关系
        StringBuilder actionBuilder = new StringBuilder();
        List<Action> actions = actionService.getActions();
        for (Action action : actions) {
            actionBuilder.append("ID: ")
                    .append(action.getId())
                    .append(", Action名: ")
                    .append(action.getHName())
                    .append(";");
        }
        String actionMapString = actionBuilder.toString();

        StringBuilder typeBuilder = new StringBuilder();
        List<TypeListResponseDto> typeListResponseDtos = typeService.queryAllType(false);
        String typeMapString = typeListResponseDtos.stream()
                .filter(type -> !type.getTName().contains("停用")) // 过滤掉含有"停用"的元素
                .map(type -> "ID: " + type.getId() + ", Type名: " + type.getTName())
                .collect(Collectors.joining(";"));

        List<AccountResponseDto> allAccount = accountService.getAllAccount();
        List<AccountResponseDto> defaultAccounts = allAccount.stream()
                .filter(account -> account.getNote().contains("默认"))
                .collect(Collectors.toList());
        Random random = new Random();
        int randomIndex = random.nextInt(defaultAccounts.size());
        AccountResponseDto randomAccount = defaultAccounts.get(randomIndex);
        int defaultAccountId = randomAccount.getId();

        GenerationResult result = qwenBean.callWithMessage(flowInfo,actionMapString,typeMapString,defaultAccountId);
        // 从响应结果中，解析处JSON，然后解析成FlowAddRequestDto对象
        String content = result.getOutput().getChoices().get(0).getMessage().getContent();
        // 根据Ai答复结果，提取JSON
        String json = extractJson(content);
        // json解析成
        Gson gson = new Gson();
        Type listType = new TypeToken<List<FlowAddRequestDto>>(){}.getType();
        return gson.fromJson(json, listType);
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
