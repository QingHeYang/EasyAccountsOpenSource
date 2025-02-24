package com.deepblue.yd_jz.service;

/**
 * @author rockyshen
 * @date 2025/2/13 13:11
 * 调用AI接口，进行拓展服务的接口
 */
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.alibaba.dashscope.exception.UploadFileException;
import com.deepblue.yd_jz.dto.FlowAddRequestDto;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
public interface AIAnalysisService {

    List<FlowAddRequestDto> analyzeFlowByAi(String filePath) throws NoApiKeyException, UploadFileException, InputRequiredException;
}
