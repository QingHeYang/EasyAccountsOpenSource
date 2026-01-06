package com.deepblue.yd_jz.config;

/**
 * @author rockyshen
 * @date 2025/2/14 22:51
 * 通义千问配置类，返回一个QwenBean，具备调用AI的能力
 * API-Key通过yml配置文件的方式传递
 */

import com.deepblue.yd_jz.utils.QwenBean;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "qwen.client")
@Data
public class QwenConfig {
    private String apiKey;

    @Bean
    public QwenBean qwenBean() {
        QwenBean qwenBean = new QwenBean(apiKey);
        return qwenBean;
    }
}
