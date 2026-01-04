package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.AccountRequestDto;
import com.deepblue.yd_jz.dto.AccountResponseDto;
import com.deepblue.yd_jz.service.AccountService;
import com.deepblue.yd_jz.dto.BaseDto;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/account")
@Tag(name = "账户管理")
public class AccountController {

    @Autowired
    AccountService accountService;

    @Operation(summary = "添加账户")
    @PostMapping("/addAccount")
    public BaseDto addAccount(@RequestBody AccountRequestDto accountRequestDto) {
        accountService.addAccount(accountRequestDto);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "更新账户")
    @PutMapping("/updateAccount/{id}")
    public BaseDto updateAccount(@PathVariable int id, @RequestBody AccountRequestDto accountRequestDto) {
        accountService.updateAccount(id, accountRequestDto);

        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "获取指定账户")
    @GetMapping("/getAccount/{id}")
    public BaseDto<AccountResponseDto> getAccount(@PathVariable int id) {
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(accountService.getAccount(id));
        return baseDto;
    }

    @Operation(summary = "获取全部账户")
    @GetMapping("/getAccount")
    public BaseDto<List<AccountResponseDto>> getAllAccount() {
        BaseDto<List<AccountResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(accountService.getAllAccount());
        return baseDto;
    }

    @GetMapping("/getAccountNoLimit")
    public BaseDto<List<AccountResponseDto>> getAllAccountNoLimit() {
        BaseDto<List<AccountResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(accountService.getAllAccountNoLimit());
        return baseDto;
    }

    @Operation(summary = "停用账户")
    @DeleteMapping("/deleteAccount/{id}")
    public BaseDto disableAccount(@PathVariable int id){
        accountService.disableAccount(id);
        return BaseDto.setSuccessBean();
    }
}
