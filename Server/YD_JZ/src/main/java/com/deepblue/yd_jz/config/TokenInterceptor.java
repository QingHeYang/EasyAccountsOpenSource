package com.deepblue.yd_jz.config;

import com.deepblue.yd_jz.service.AuthConfigService;
import com.deepblue.yd_jz.utils.AuthUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

// v2.7.0 (config-ui): 拦截器始终注册（见 WebConfig）；进入时现读 AuthConfigService.isLoginEnable() 决定放行
// 不缓存登录开关，每次请求实时反映 DB 配置；用户在 UI 切换登录开关后下一个请求即生效
@Slf4j
public class TokenInterceptor implements HandlerInterceptor {

    private final AuthUtils authUtils;
    private final AuthConfigService authConfigService;

    public TokenInterceptor(AuthUtils authUtils, AuthConfigService authConfigService) {
        this.authUtils = authUtils;
        this.authConfigService = authConfigService;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        log.debug("TokenInterceptor preHandle called for URI: {}", request.getRequestURI());

        // 现读 DB 配置；登录功能关闭时直接放行
        if (!authConfigService.isLoginEnable()) {
            log.debug("Authentication is disabled. Allowing request: {}", request.getRequestURI());
            return true;
        }

        String uri = request.getRequestURI();
        String token = request.getHeader("Authorization");
        log.debug("Authorization token: {}", token);

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
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) throws Exception {
    }
}
