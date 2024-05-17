package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.controller.flow.FlowBaseBean;
import com.deepblue.yd_jz.controller.flow.FlowGetBean;
import com.deepblue.yd_jz.controller.flow.FlowToClientBean;
import com.deepblue.yd_jz.dao.account.Account;
import com.deepblue.yd_jz.dao.account.AccountDao;
import com.deepblue.yd_jz.dao.action.Action;
import com.deepblue.yd_jz.dao.action.ActionDao;
import com.deepblue.yd_jz.dao.flow.Flow;
import com.deepblue.yd_jz.dao.flow.FlowDao;
import com.deepblue.yd_jz.dao.type.Type;
import com.deepblue.yd_jz.dao.type.TypeDao;
import com.deepblue.yd_jz.utils.ContentValues;
import com.deepblue.yd_jz.utils.FileMakeWebHook;
import com.deepblue.yd_jz.utils.LogUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class FlowService {

    @Autowired
    ActionDao actionDao;

    @Autowired
    AccountDao accountDao;

    @Autowired
    FlowDao flowDao;

    @Autowired
    TypeDao typeDao;


    @Transactional(rollbackFor = Exception.class)
    public void doAddFlow(FlowGetBean flowGetBean) throws Exception {
        String log = "新增flow\n"+"金额： "+flowGetBean.getMoney()+"";
        LogUtils.log_print(log);
        Flow flow = setNewFlow(flowGetBean);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd hh:mm:ss");
        String createDate = sdf.format(new Date());
        flow.setfCreateDate(createDate);
        BeanUtils.copyProperties(flowGetBean, flow);
        flowDao.addFlow(flow);
    }

    private Flow setNewFlow(FlowGetBean flowGetBean) throws Exception {
        Action action = actionDao.getActionSingle(flowGetBean.getActionId()).get(0);
        Account account = accountDao.queryAccount(flowGetBean.getAccountId() + "").get(0);
        Account toAccount = null;
        BigDecimal flowMoney = new BigDecimal(flowGetBean.getMoney());
        BigDecimal accountMoney = new BigDecimal(account.getMoney());
        switch (action.getHandle()) {
            case ContentValues.ACTION_ADD:
                account = handleAccount(ContentValues.ACTION_ADD, flowGetBean.getMoney(), account, action.isExempt());
                break;
            case ContentValues.ACTION_SUB:
                if (accountMoney.compareTo(flowMoney) < 0) {
                    throw new Exception("减少金额不允许大于账户金额");
                }
                account = handleAccount(ContentValues.ACTION_SUB, flowGetBean.getMoney(), account, action.isExempt());
                break;
            case ContentValues.ACTION_INNER:
                if (accountMoney.compareTo(flowMoney) < 0) {
                    throw new Exception("减少金额不允许大于账户金额");
                }
                toAccount = accountDao.queryAccount(flowGetBean.getAccountToId() + "").get(0);
                toAccount = handleAccount(ContentValues.ACTION_ADD, flowGetBean.getMoney(), toAccount, action.isExempt());
                accountDao.updateAccount(toAccount);
                account = handleAccount(ContentValues.ACTION_SUB, flowGetBean.getMoney(), account, action.isExempt());
                break;
        }
        accountDao.updateAccount(account);

        Flow flow = new Flow();
        flow.setExempt(action.isExempt());
        BeanUtils.copyProperties(flowGetBean, flow);
        return flow;
    }

    @Transactional(rollbackFor = Exception.class)
    public void doUpdateFlowCollect(int id,int collect) {
        flowDao.updateFlowCollect(id, collect);
    }
    public void doCollectFlow(int id, int collect){
        flowDao.collectFlowById(id,collect);
    }

    @Transactional(rollbackFor = Exception.class)
    public void doUpdateFlow(int id, FlowGetBean flowGetBean) throws Exception {
        String log = "更新flow\n"+"id: "+id+"\n金额： "+flowGetBean.getMoney()+"\n原操作： ";
        Flow lastFlow = flowDao.queryFlowById(id).get(0);
        Action lastAction = actionDao.getActionSingle(lastFlow.getActionId()).get(0);
        Account lastAccount = accountDao.queryAccount(lastFlow.getAccountId() + "").get(0);
        switch (lastAction.getHandle()) {
            case ContentValues.ACTION_ADD:
                log = log+"金额增加\n";
                lastAccount = handleAccount(ContentValues.ACTION_SUB, lastFlow.getMoney(), lastAccount, lastAction.isExempt());
                break;
            case ContentValues.ACTION_SUB:
                log = log+"金额减少\n";
                lastAccount = handleAccount(ContentValues.ACTION_ADD, lastFlow.getMoney(), lastAccount, lastAction.isExempt());
                break;
            case ContentValues.ACTION_INNER:
                log = log+"内部转账\n";
                Account lastToAccount = accountDao.queryAccount(lastFlow.getAccountToId() + "").get(0);
                lastToAccount = handleAccount(ContentValues.ACTION_SUB, lastFlow.getMoney(), lastToAccount, lastAction.isExempt());
                accountDao.updateAccount(lastToAccount);
                lastAccount = handleAccount(ContentValues.ACTION_ADD, lastFlow.getMoney(), lastAccount, lastAction.isExempt());
                break;
        }
        LogUtils.log_print(log);
        accountDao.updateAccount(lastAccount);
        Flow flow = setNewFlow(flowGetBean);
        flow.setId(id);
        BeanUtils.copyProperties(flowGetBean, flow);
        flowDao.updateFlow(flow);
    }

    private Account handleAccount(int handle, String money, Account account, boolean isExempt) {
        String log = "账户操作日志\n"+"账户名称： "+account.getaName()+"\n原始金额： "+account.getMoney()+"\n操作金额： "+money+"\n当前操作： ";
        BigDecimal flowMoney = new BigDecimal(money);
        BigDecimal accountMoney = new BigDecimal(account.getMoney());
        BigDecimal accountExemptMoney = isExempt ? new BigDecimal(account.getExemptMoney()) : null;
        switch (handle) {
            case ContentValues.ACTION_ADD:
                log=log+"+\n";
                accountMoney = accountMoney.add(flowMoney);
                if (isExempt) {
                    accountExemptMoney = accountExemptMoney.add(flowMoney);
                    account.setExemptMoney(accountExemptMoney.toString());
                }
                break;
            case ContentValues.ACTION_SUB:
                log=log+"-\n";
                accountMoney = accountMoney.subtract(flowMoney);
                if (isExempt) {
                    accountExemptMoney = accountExemptMoney.subtract(flowMoney);
                    account.setExemptMoney(accountExemptMoney.toString());
                }
                break;
        }
        account.setMoney(accountMoney.toString());
        log=log+"结转金额： "+account.getMoney();
        LogUtils.log_print(log);
        return account;
    }

    @Transactional(rollbackFor = Exception.class)
    public FlowToClientBean doQueryFlow(int id) {
        String log = "查询flow\n"+"id： "+id+"";
        List<Flow> flows = flowDao.queryFlowById(id);
        if (flows == null || flows.size() == 0) {
            return null;
        }
        FlowToClientBean toClientBean = new FlowToClientBean();
        Flow flow = flows.get(0);
        BeanUtils.copyProperties(flow, toClientBean);
        Account account = accountDao.queryAccount(flow.getAccountId() + "").get(0);
        Action action = actionDao.getActionSingle(flow.getActionId()).get(0);
        Type type = typeDao.queryTypeSingle(flow.getTypeId()).get(0);
        if (type.getParent() != -1) {
            Type parentType = typeDao.queryTypeSingle(type.getParent()).get(0);
            type.settName(parentType.gettName() + "——" + type.gettName());
        }
        if (action.getHandle() == ContentValues.ACTION_INNER) {
            Account toAccount = accountDao.queryAccount(flow.getAccountToId() + "").get(0);
            toClientBean.setAccountTo(toAccount);
        }
        toClientBean.setType(type);
        toClientBean.setAccount(account);
        toClientBean.setAction(action);
        LogUtils.log_print(log);
        LogUtils.log_json(toClientBean);
        return toClientBean;
    }

    @Transactional(rollbackFor = Exception.class)
    public void doDeleteFlow(int id) throws Exception {
        String log = "删除flow\n"+"id： "+id+"";
        LogUtils.log_print(log);
        Flow flow = flowDao.queryFlowById(id).get(0);
        Action lastAction = actionDao.getActionSingle(flow.getActionId()).get(0);
        Account lastAccount = accountDao.queryAccount(flow.getAccountId() + "").get(0);
        switch (lastAction.getHandle()) {
            case ContentValues.ACTION_ADD:
                lastAccount = handleAccount(ContentValues.ACTION_SUB, flow.getMoney(), lastAccount, lastAction.isExempt());
                break;
            case ContentValues.ACTION_SUB:
                lastAccount = handleAccount(ContentValues.ACTION_ADD, flow.getMoney(), lastAccount, lastAction.isExempt());
                break;
            case ContentValues.ACTION_INNER:
                Account lastToAccount = accountDao.queryAccount(flow.getAccountToId() + "").get(0);
                lastToAccount = handleAccount(ContentValues.ACTION_SUB, flow.getMoney(), lastToAccount, lastAction.isExempt());
                accountDao.updateAccount(lastToAccount);
                lastAccount = handleAccount(ContentValues.ACTION_ADD, flow.getMoney(), lastAccount, lastAction.isExempt());
                break;
        }

        accountDao.updateAccount(lastAccount);
        flowDao.deleteFlowById(id);
    }

    @Transactional(rollbackFor = Exception.class)
    public FlowBaseBean doGetMainBean(int handle, int order, String date) {
        String monthStr = date.substring(0, 7) + "%";
        FlowBaseBean flowBaseBean = new FlowBaseBean();
        SimpleDateFormat sdf1 = new SimpleDateFormat("yyyyMMdd_HHmm");
        String time = sdf1.format(new Date());
        log.info("time:  "+time+"   date: " + monthStr + "  handle: " + handle);
        List<Map<String, Object>> maps = flowDao.getFlowByMain(handle, order, monthStr) ;
        List<FlowBaseBean.FlowInnerBean> flows = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        BigDecimal moneyIn = new BigDecimal("0");
        BigDecimal moneyOut = new BigDecimal("0");
        for (Map<String, Object> map : maps) {
            FlowBaseBean.FlowInnerBean flow = new FlowBaseBean.FlowInnerBean();
            flow.setId((Integer) map.get("id"));
            flow.setMoney((String) map.get("money"));
            flow.setExempt((Boolean) map.get("exempt"));
            flow.setCollect((Boolean) map.get("collect"));
            flow.setHandle((Integer) map.get("handle"));
            flow.sethName((String) map.get("h_name"));
            Date fDate = (Date) map.get("f_date");

            flow.setfDate(sdf.format(fDate));
            flow.setaName((String) map.get("a_name"));
            flow.setNote((String) map.get("note"));
            flow.setToAName((String) map.get("t_a_name"));

            if (map.get("p_t_name") != null) {
                flow.settName(map.get("p_t_name") + "/" + map.get("t_name"));
            } else {
                flow.settName((String) map.get("t_name"));
            }
            flows.add(flow);
            if (flow.getHandle() == 1) {
                moneyOut = moneyOut.add(new BigDecimal(flow.getMoney()));
            } else if (flow.getHandle() == 0) {
                moneyIn = moneyIn.add(new BigDecimal(flow.getMoney()));
            }
        }

        flowBaseBean.setTotalIn(moneyIn.toString());
        flowBaseBean.setTotalOut(moneyOut.toString());
        flowBaseBean.setFlows(flows);
        return flowBaseBean;
    }

}
