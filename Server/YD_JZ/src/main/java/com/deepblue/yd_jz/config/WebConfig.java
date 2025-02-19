package com.deepblue.yd_jz.config;
import com.deepblue.yd_jz.utils.AuthUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import org.springframework.context.annotation.Bean;
import org.springframework.web.filter.CorsFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${auth.enable}")
    private boolean authEnable;

    @Autowired
    private AuthUtils authUtils;

    @Bean
    public TokenInterceptor tokenInterceptor() {
        return new TokenInterceptor(authEnable, authUtils);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        if (authEnable) {
            registry.addInterceptor(tokenInterceptor())
                    .addPathPatterns("/**")
                    .excludePathPatterns(
                            "/swagger-ui.html",
                            "/swagger-ui/**",
                            "/v2/api-docs",
                            "/swagger-resources/**",
                            "/webjars/**",
                            "/auth/login",
                            "/auth/register",
                            "/error" // 排除 /error 路径
                    );
        }
    }


    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();

        CorsConfiguration config = new CorsConfiguration();

        // 允许跨域的头部信息
        config.addAllowedHeader("*");
        // 允许跨域的方法
        config.addAllowedMethod("*");
        // 可访问的外部域
        config.addAllowedOrigin("*");
        // 需要跨域用户凭证（cookie、HTTP认证及客户端SSL证明等）
        //config.setAllowCredentials(true);
        //config.addAllowedOriginPattern("*");

        // 跨域路径配置
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
