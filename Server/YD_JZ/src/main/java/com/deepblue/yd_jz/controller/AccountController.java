package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.AccountRequestDto;
import com.deepblue.yd_jz.dto.AccountResponseDto;
import com.deepblue.yd_jz.service.AccountService;
import com.deepblue.yd_jz.dto.BaseDto;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/account")
@Api(value = "AccountController", tags = {"账户管理"})
public class AccountController {

    @Autowired
    AccountService accountService;

    @ApiOperation(value = "添加账户")
    @PostMapping("/addAccount")
    public BaseDto addAccount(@RequestBody AccountRequestDto accountRequestDto) {
        accountService.addAccount(accountRequestDto);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "更新账户")
    @PutMapping("/updateAccount/{id}")
    public BaseDto updateAccount(@PathVariable int id, @RequestBody AccountRequestDto accountRequestDto) {
        accountService.updateAccount(id, accountRequestDto);

        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "获取指定账户")
    @GetMapping("/getAccount/{id}")
    public BaseDto<AccountResponseDto> getAccount(@PathVariable int id) {
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(accountService.getAccount(id));
        return baseDto;
    }

    @ApiOperation(value = "获取全部账户")
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

    @ApiOperation(value = "停用账户")
    @DeleteMapping("/deleteAccount/{id}")
    public BaseDto disableAccount(@PathVariable int id){
        accountService.disableAccount(id);
        return BaseDto.setSuccessBean();
    }
}
