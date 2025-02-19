package com.deepblue.yd_jz.config;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.service.AuthService;
import com.deepblue.yd_jz.utils.AuthUtils;
import com.deepblue.yd_jz.utils.ContentValues;
import com.deepblue.yd_jz.utils.GsonUtils;
import lombok.extern.slf4j.Slf4j;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.File;
import java.io.IOException;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.servlet.HandlerInterceptor;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Slf4j
public class TokenInterceptor implements HandlerInterceptor {

    private boolean authEnable;
    private AuthUtils authUtils;

    // 构造函数注入依赖
    public TokenInterceptor(boolean authEnable, AuthUtils authUtils) {
        this.authEnable = authEnable;
        this.authUtils = authUtils;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        log.debug("TokenInterceptor preHandle called for URI: {}", request.getRequestURI());

        if (!authEnable) {
            log.debug("Authentication is disabled. Allowing request: {}", request.getRequestURI());
            return true;
        }

        String uri = request.getRequestURI();

        // 拦截器中移除 Swagger 和登录注册路径的过滤逻辑
        // 这些逻辑现在由 WebConfig 的 excludePathPatterns 处理

        String token = request.getHeader("Authorization");
        log.debug("Authorization token: {}", token);

        // 进行token验证，并处理验证结果
        int code = authUtils.isAuth(token);
        if (code == 200) {
            log.debug("Authentication successful for URI: {}", uri);
            return true;
        } else {
            log.warn("Authentication failed for URI: {} with code: {}", uri, code);
            String errorMsg = "";
            if (code == 401) {
                errorMsg = "需要登录";
            } else if (code == 418) {
                errorMsg = "需要注册";
            }
            response.sendError(code, errorMsg);
            return false;
        }
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler,
                           ModelAndView modelAndView) throws Exception {
        // 请求处理后的逻辑
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) throws Exception {
        // 请求完成后的逻辑
    }
}
