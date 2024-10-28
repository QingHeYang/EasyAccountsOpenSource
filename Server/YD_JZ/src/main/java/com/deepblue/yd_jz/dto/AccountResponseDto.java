package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.Account;
import lombok.Data;

import java.text.SimpleDateFormat;

@Data
public class AccountResponseDto {
    private int id;
    private String name;
    private String money;
    private String exemptMoney;
    private String card;
    private String createTime;
    private String note;

    public AccountResponseDto convertToDto(Account account) {
        if (account == null) {
            return this;
        }
        AccountResponseDto accountResponseDto = this;
        accountResponseDto.setId(account.getId());
        if (account.getDisable()){
            accountResponseDto.setName(account.getAName()+"(已停用)");
        }else {
            accountResponseDto.setName(account.getAName());
        }
        accountResponseDto.setMoney(account.getMoney());
        accountResponseDto.setExemptMoney(account.getExemptMoney());
        accountResponseDto.setCard(account.getCard());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        accountResponseDto.setCreateTime(sdf.format(account.getCreateTime()));
        accountResponseDto.setNote(account.getNote());
        return accountResponseDto;
    }
}
