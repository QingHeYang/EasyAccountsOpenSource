package com.deepblue.yd_jz.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {
    public static final String AUTHORIZATION_HEADER = "Authorization";

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .components(new Components()
                        .addSecuritySchemes("UUID", new SecurityScheme()
                                .type(SecurityScheme.Type.APIKEY)
                                .in(SecurityScheme.In.HEADER)
                                .name(AUTHORIZATION_HEADER)))
                .addSecurityItem(new SecurityRequirement().addList("UUID"))
                .info(new Info()
                        .title("EasyAccounts后台接口")
                        .description("下列接口均为nginx前端请求使用接口")
                        .version("v2.6.0")
                        .contact(new Contact()
                                .name("Mercy")
                                .url("https://github.com/QingHeYang/EasyAccounts"))
                        .license(new License()
                                .name("MIT License")
                                .url("https://github.com/QingHeYang/EasyAccounts?tab=MIT-1-ov-file")));
    }
}
