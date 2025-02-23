package com.deepblue.yd_jz.utils;

/**
 * @author rockyshen
 * @date 2025/2/14 15:19
 * 调用 阿里通义千问 API
 */

import com.alibaba.dashscope.aigc.generation.Generation;
import com.alibaba.dashscope.aigc.generation.GenerationParam;
import com.alibaba.dashscope.aigc.generation.GenerationResult;
import com.alibaba.dashscope.aigc.multimodalconversation.MultiModalConversation;
import com.alibaba.dashscope.aigc.multimodalconversation.MultiModalConversationParam;
import com.alibaba.dashscope.aigc.multimodalconversation.MultiModalConversationResult;
import com.alibaba.dashscope.common.Message;
import com.alibaba.dashscope.common.MultiModalMessage;
import com.alibaba.dashscope.common.Role;
import com.alibaba.dashscope.exception.ApiException;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.alibaba.dashscope.exception.UploadFileException;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class QwenBean {
    private String apiKey;

    public QwenBean(String apiKey) {
        this.apiKey = apiKey;
    }

    public String ocrConversationCall(String filePath)
            throws ApiException, NoApiKeyException, UploadFileException {
        MultiModalConversation conv = new MultiModalConversation();
        Map<String, Object> map = new HashMap<>();
        map.put("image", filePath);
        map.put("max_pixels", "1003520");
        map.put("min_pixels", "3136");
        MultiModalMessage userMessage = MultiModalMessage.builder().role(Role.USER.getValue())
                .content(Arrays.asList(
                        map,
                        //为保证识别效果，目前模型内部会统一使用"Read all the text in the image."进行识别，用户输入的文本不会生效。
                        Collections.singletonMap("text", "Read all the text in the image."))).build();
        MultiModalConversationParam param = MultiModalConversationParam.builder()
                // 若没有配置环境变量，请用百炼API Key将下行替换为：.apiKey("sk-xxx")
//                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .apiKey(apiKey)
                .model("qwen-vl-ocr")
                .message(userMessage)
                .build();
        MultiModalConversationResult result = conv.call(param);

//        System.out.println(result.getOutput().getChoices().get(0).getMessage().getContent().get(0).get("text"));

        // 提取字符串数据
        String extractedText = "";
        try {
            // 假设 result 是一个包含你的数据结构的对象
            extractedText = (String) result.getOutput()
                    .getChoices()
                    .get(0)
                    .getMessage()
                    .getContent()
                    .get(0)
                    .get("text");

//            System.out.println("OCR提取到的账单信息  ==>  "+extractedText);

        } catch (NullPointerException | IndexOutOfBoundsException e) {
            // 处理潜在的异常，例如链式调用中遇到的 Null 或 Index 问题
            System.err.println("Error extracting text: " + e.getMessage());
            // 可能返回一个默认值或错误指示符
            extractedText = "Error: Unable to extract text.";
        }

        return extractedText;
    }

    // TODO 考虑追加提示词，例如：后续不要把消费金额为“¥0.00"的加入流水，添加提示词的入口，可以放在setting页！
    public GenerationResult callWithMessage(String flowInfo, String actionMapString, String typeMapString, Integer defaultAccountId) throws ApiException, NoApiKeyException, InputRequiredException {
        // 获取当前日期
        LocalDate today = LocalDate.now();

        // 根据需要格式化日期为 'YYYY-MM'
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        String formattedDate = today.format(formatter);

        // 1、今天的日期：系统获取后传入
        // 2、type与id的映射，action与id的映射，由外部查询后传入，而不是硬编码！
        String prompt =
                "以上是提供给你文字版的账单内容，请你分析账单内容，每一条消费记录，请你封装进如下 JSON 格式中，如果有多条就整合成一个列表输出你的回复\n" +
                        "{\n" +
                        "    \"money\": \"消费金额\",\n" +
                        "    \"fDate\": \"账单日期\",\n" +
                        "    \"createDate\": \"默认为空，不用生成\",\n" +
                        "    \"actionId\": \"根据我提供的action和id的对应关系进行判断，输入Int类型，而不是String类型，如果不确定就选支出\",\n" +
                        "    \"accountId\": \"默认为" + defaultAccountId + "\",\n" +
                        "    \"accountToId\": \"默认为0\",\n" +
                        "    \"typeId\": \"根据我下文提供的类别和id的对应关系进行判断，输入Int类型，而不是String类型\",\n" +
                        "    \"isCollect\": \"这是Boolean类型，统一给默认值为false\",\n" +
                        "    \"note\": \"消费记录的详情\"\n" +
                        "}\n" +
                        "以下是一些补充信息：\n" +
                        "1、如果图片识别出来和账单无关，note写入“未识别到账单信息！”，其余JSON字段全部设置为空的，千万不要生成虚假数据！\n" +
                        "2、当账单金额为减号加一个数字（例如：“-298.00”），表示行为是“支出”，记录在money字段时，去掉负号，只保留金额（例如：“298.00”）\n" +
                        "3、注意每个字段的类型，应该为Int或Boolean类型的，我已经在示例中声明了；\n" +
                        "4、fDate为账单日期，我告诉你今天是" + formattedDate + "，例如文本中的“今天14:00”，请按照“yyyy-MM-dd”的格式生成，忽略时间；\n" +
                        "5、action行为与actionId的对应关系是：" + actionMapString + "\n" +
                        "6、type类别与typeId的对应关系是，" + typeMapString + "\n你识别不了的消费记录，可以归到“其他”类别下。";

        Generation gen = new Generation();
        Message systemMsg = Message.builder()
                .role(Role.SYSTEM.getValue())
                .content("You are a helpful assistant.")
                .build();
        Message userMsg = Message.builder()
                .role(Role.USER.getValue())
                .content(flowInfo + prompt)
                .build();
        GenerationParam param = GenerationParam.builder()
                // 若没有配置环境变量，请用百炼API Key将下行替换为：.apiKey("sk-xxx")
//                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .apiKey(apiKey)
                // 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
                .model("qwen-plus")
                .messages(Arrays.asList(systemMsg, userMsg))
                .resultFormat(GenerationParam.ResultFormat.MESSAGE)
                .build();
        return gen.call(param);
    }
}
