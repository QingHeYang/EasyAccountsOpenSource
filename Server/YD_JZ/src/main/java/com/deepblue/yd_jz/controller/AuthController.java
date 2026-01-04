package com.deepblue.yd_jz.controller;


import com.deepblue.yd_jz.dto.AuthDto;
import com.deepblue.yd_jz.dto.AuthRequestDto;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.entity.Auth;
import com.deepblue.yd_jz.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@Tag(name = "登录注册")
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

    @Operation(summary = "登录")
    @PostMapping("/login")
    public BaseDto login(@RequestBody AuthRequestDto authRequestDto) {
        if (!authService.verfiyAuthFiles()) {
            return BaseDto.setErrorBean("用户名密码不存在，请注册",418);
        }
        AuthDto authDto = authService.login(authRequestDto.getUsername(), authRequestDto.getPassword());
        if (authDto == null) {
            return BaseDto.setErrorBean("用户名或密码错误",401);
        }
        BaseDto<AuthDto> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(authDto);
        return baseDto;
    }

    @Operation(summary = "注册")
    @PostMapping("/register")
    public BaseDto register(@RequestBody AuthRequestDto authRequestDto) {
        AuthDto authDto = authService.register(authRequestDto.getUsername(), authRequestDto.getPassword());
        if (authDto == null) {
            return BaseDto.setErrorBean("已存在用户名和密码，忘记密码请重置",401);
        }
        BaseDto<AuthDto> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(authDto);
        return baseDto;
    }
}