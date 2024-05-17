package com.deepblue.yd_jz.controller.account;

import com.deepblue.yd_jz.dao.account.Account;
import com.deepblue.yd_jz.service.AccountService;
import com.deepblue.yd_jz.utils.DataBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

@RestController
@RequestMapping("/account")
public class AccountController {

    @Autowired
    AccountService accountService;

    @PostMapping("/addAccount")
    public DataBean addAccount(@RequestBody AccountPostBean accountPostBean) {
        accountService.addAccount(accountPostBean);
        return DataBean.setSuccessBean();
    }

    @PutMapping("/updateAccount/{id}")
    public DataBean updateAccount(@PathVariable int id, @RequestBody AccountPostBean accountPostBean) {
        accountService.updateAccount(id, accountPostBean);

        return DataBean.setSuccessBean();
    }

    @GetMapping("/getAccount/{id}")
    public DataBean<AccountToClient> getAccount(@PathVariable int id) {
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(accountService.getAccount(id));
        return dataBean;
    }

    @GetMapping("/getAccount")
    public DataBean<List<AccountToClient>> getAllAccount() {
        DataBean<List<AccountToClient>> dataBean = DataBean.setSuccessBean();
        dataBean.setData(accountService.getAllAccount());
        return dataBean;
    }

    @DeleteMapping("/deleteAccount/{id}")
    public DataBean disableAccount(@PathVariable int id){
        accountService.disableAccount(id);
        return DataBean.setSuccessBean();
    }
}
