package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.controller.account.AccountToClient;
import com.deepblue.yd_jz.dao.account.Account;
import com.deepblue.yd_jz.controller.account.AccountPostBean;
import com.deepblue.yd_jz.dao.account.AccountDao;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Service
public class AccountService {

    @Autowired
    AccountDao accountDao;

    @Transactional(rollbackFor = Exception.class)
    public void addAccount(AccountPostBean postBean) {
        Account account = new Account();
        BeanUtils.copyProperties(postBean, account);
        account.setaName(postBean.getName());
        account.setExemptMoney(postBean.getExemptMoney());
        account.setaDisable(false);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        account.setCreateTime(sdf.format(new Date()));
        accountDao.addAccount(account);
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateAccount(int id, AccountPostBean postBean) {
        Account account = new Account();
        BeanUtils.copyProperties(postBean, account);
        account.setaName(postBean.getName());
        account.setExemptMoney(postBean.getExemptMoney());
        account.setId(id);
        accountDao.updateAccount(account);
    }

    @Transactional(rollbackFor = Exception.class)
    public AccountToClient getAccount(int id) {
        AccountToClient accountToClient = new AccountToClient();
        List<Account> accounts = accountDao.queryAccount(id + "");
        Account account = accounts.get(0);
        BeanUtils.copyProperties(account, accountToClient);
        accountToClient.setName(account.getaName());
        return accountToClient;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<AccountToClient> getAllAccount() {
        List<Account> accounts = accountDao.queryAllAccount();
        List<AccountToClient> accountToClients = new ArrayList<>();
        for (Account a : accounts) {
            AccountToClient toClient = new AccountToClient();
            BeanUtils.copyProperties(a, toClient);
            toClient.setName(a.getaName());
            accountToClients.add(toClient);
        }
        return accountToClients;
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableAccount(int id) {
        accountDao.disableAccount(id+"");
    }

    /*@Transactional(rollbackFor = Exception.class)
    public void disableAccount(int id) {

    }*/
}
