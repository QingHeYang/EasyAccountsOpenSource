package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.FlowRepository;
import com.deepblue.yd_jz.dto.AccountResponseDto;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.dto.AccountRequestDto;
import com.deepblue.yd_jz.dao.jpa.AccountRepository;
import com.deepblue.yd_jz.entity.Flow;
import com.deepblue.yd_jz.entity.FlowJpaEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

import static com.deepblue.yd_jz.utils.ContentValues.*;

@Slf4j
@Service
public class AccountService {

    @Autowired
    private AccountRepository accountRepository;
    @Autowired
    private FlowTemplateService flowTemplateService;

    @Autowired
    private FlowRepository flowRepository;

    @Transactional(rollbackFor = Exception.class)
    public void addAccount(AccountRequestDto postBean) {
        Account account = new Account();
        BeanUtils.copyProperties(postBean, account);
        account.setAName(postBean.getName());
        account.setExemptMoney(postBean.getExemptMoney());
        account.setDisable(false);
        account.setCreateTime(new Date());
        accountRepository.save(account);
    }


    @Transactional(rollbackFor = Exception.class)
    public void updateAccount(int id, AccountRequestDto postBean) {
        Account account = accountRepository.findById(id).orElse(null);
        if (account != null) {
            BeanUtils.copyProperties(postBean, account);
            account.setAName(postBean.getName());
            accountRepository.save(account);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public AccountResponseDto getAccount(int id) {
        Account account = accountRepository.findById(id).orElse(null);
        if (account != null) {
            AccountResponseDto accountResponseDto = new AccountResponseDto();
            BeanUtils.copyProperties(account, accountResponseDto);
            accountResponseDto.setName(account.getAName());
            return accountResponseDto;
        }
        return null;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<AccountResponseDto> getAllAccountNoLimit() {
        List<Account> accounts = accountRepository.findAll();
        List<AccountResponseDto> accountResponseDtos = new ArrayList<>();
        for (Account a : accounts) {
            AccountResponseDto toClient = new AccountResponseDto();
            toClient.convertToDto(a);
            accountResponseDtos.add(toClient);
        }
        return accountResponseDtos;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<AccountResponseDto> getAllAccount() {
        List<Account> accounts = accountRepository.findByDisableFalse();  // 获取所有未禁用的账户
        List<AccountResponseDto> accountResponseDtos = new ArrayList<>();
        for (Account a : accounts) {
            AccountResponseDto toClient = new AccountResponseDto();
            BeanUtils.copyProperties(a, toClient);  // 将 Account 实体的属性复制到 AccountToClient
            toClient.setName(a.getAName());  // 特别设置名称，假设 AccountToClient 有不同的属性名
            accountResponseDtos.add(toClient);  // 将处理后的对象添加到列表中
        }
        return accountResponseDtos;  // 返回转换后的客户端可见的账户列表
    }

    /**
     * 通过日期获取账户时间节点的账户信息
     * @param date
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    public List<Account> getAccountByDate(String date) {
        List<Account>  accounts= getAllOriginAccounts();
        List<Account> cloneList = accounts.stream()
                .map(account -> cloneAccount(account))
                .collect(Collectors.toList());
        HashMap<Integer, Account> accountMap = new HashMap<>();
        for (Account account : cloneList) {
            accountMap.put(account.getId(), account);
        }
        List<FlowJpaEntity> flows = flowRepository.findByFDateAfter(date);
        log.info("flows size: " + flows.size());
        for (FlowJpaEntity flow : flows) {
            Account account = accountMap.get(flow.getAccountId());
            switch (flow.getAction().getHandle()){
                case ACTION_ADD:
                    account.setMoney(reverseMoney(account.getMoney(), flow.getMoney(), ACTION_ADD).toString());
                    break;
                case ACTION_SUB:
                    account.setMoney(reverseMoney(account.getMoney(), flow.getMoney(), ACTION_SUB).toString());
                    break;
                case ACTION_INNER:
                    log.info("内部转账：从"
                            +account.getAName()
                            +"转账到"+accountMap.get(flow.getAccountToId()).getAName()
                            +"  金额："+flow.getMoney());
                    account.setMoney(reverseMoney(account.getMoney(), flow.getMoney(), ACTION_SUB).toString());
                    Account accountTo = accountMap.get(flow.getAccountToId());
                    accountTo.setMoney(reverseMoney(accountTo.getMoney(), flow.getMoney(), ACTION_ADD).toString());
                    break;
            }
        }
        ArrayList<Account> accountList = new ArrayList<>(accountMap.values());
        return accountList;
    }

    /**
     * 深度克隆一个账户对象
     * @param managed
     * @return
     */
    private Account cloneAccount(Account managed) {
        Account detached = new Account();
        detached.setAName(managed.getAName());
        detached.setCreateTime(managed.getCreateTime());
        detached.setId(managed.getId());
        detached.setMoney(managed.getMoney());
        // 视情况复制其他字段
        return detached;
    }

    /**
     * 反转金额
     * @param accountsMoneyStr
     * @param money
     * @param handle
     * @return
     */
    private String reverseMoney(String accountsMoneyStr, String money, int handle) {
        BigDecimal accountsMoney = new BigDecimal(accountsMoneyStr);
        BigDecimal moneyDecimal = new BigDecimal(money);
        if (handle == ACTION_ADD) {
            return accountsMoney.subtract(moneyDecimal).toString();
        } else {
            return accountsMoney.add(moneyDecimal).toString();
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableAccount(int id) {
        // 使用 JPA 的 findById 方法查找账户
        accountRepository.findById(id).ifPresent(account -> {
            account.setDisable(true);  // 设置账户为禁用状态
            accountRepository.save(account);  // 保存更改
            flowTemplateService.clearAccount(id);  // 清除与该账户相关的流程模板
        });
    }

    @Transactional(rollbackFor = Exception.class)
    public Account getOriginAccountById(int id) {
        // 从数据库中获取并返回Account实体，如果找不到则返回null
        return accountRepository.findById(id).orElse(null);
    }

    @Transactional(readOnly = true)  // 使用只读事务，因为这是一个查询操作
    public List<Account> getAllOriginAccounts() {
        return accountRepository.findAll();  // 调用 JPA 的 findAll() 获取所有账户记录
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateOriginAccount(Account account) {
        accountRepository.save(account);  // 保存更新后的Account实体
    }


    /*@Transactional(rollbackFor = Exception.class)
    public void disableAccount(int id) {

    }*/
}
