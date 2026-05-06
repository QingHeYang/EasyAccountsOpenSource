package com.deepblue.yd_jz.config;

import com.deepblue.yd_jz.service.AuthConfigService;
import com.deepblue.yd_jz.utils.AuthUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

// v2.7.0 (config-ui): 始终注册拦截器，由拦截器内部现读 AuthConfigService.isLoginEnable() 实时决定放行
// 改造前：if (authEnable) registry.addInterceptor(...) —— 启动期决定，切换需要重启
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Autowired
    private AuthUtils authUtils;

    @Autowired
    private AuthConfigService authConfigService;

    @Bean
    public TokenInterceptor tokenInterceptor() {
        return new TokenInterceptor(authUtils, authConfigService);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 始终注册：登录开关动态读 DB，关掉时拦截器内部直接放行
        registry.addInterceptor(tokenInterceptor())
                .addPathPatterns("/**")
                .excludePathPatterns(
                        // SpringDoc OpenAPI 3 路径
                        "/docs",
                        "/docs/**",
                        "/swagger-ui.html",
                        "/swagger-ui/**",
                        "/v3/api-docs",
                        "/v3/api-docs/**",
                        "/webjars/**",
                        // 业务路径
                        "/auth/login",
                        "/auth/register",
                        "/error",
                        "/image/**"
                );
    }

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();

        CorsConfiguration config = new CorsConfiguration();
        config.addAllowedHeader("*");
        config.addAllowedMethod("*");
        config.addAllowedOrigin("*");

        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
