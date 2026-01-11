package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.FlowListDto;
import com.deepblue.yd_jz.dto.FlowAddRequestDto;
import com.deepblue.yd_jz.dto.FlowSingleResponseDto;
import com.deepblue.yd_jz.dto.TypeListResponseDto;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.entity.Flow;
import com.deepblue.yd_jz.entity.FlowImage;
import com.deepblue.yd_jz.dao.mybatis.FlowDao;
import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.ContentValues;
import com.deepblue.yd_jz.utils.LogUtils;
import com.deepblue.yd_jz.utils.MoneyUtils;
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
    ActionService actionService;

    @Autowired
    AccountService accountService;

    @Autowired
    FlowDao flowDao;

    @Autowired
    TypeService typeService;

    @Autowired
    TypeRepository typeRepository;

    @Autowired
    ImageService imageService;


    @Transactional(rollbackFor = Exception.class)
    public int doAddFlow(FlowAddRequestDto flowAddRequestDto) throws Exception {
        // 格式化金额，确保只有2位小数
        flowAddRequestDto.setMoney(MoneyUtils.formatMoney(flowAddRequestDto.getMoney()));

        // 校验分类：有子分类且定义了actionId的父分类不允许直接记账
        List<Type> subTypes = typeRepository.findByParent(flowAddRequestDto.getTypeId());
        if (subTypes != null && !subTypes.isEmpty()) {
            // v2.6.0: 只有定义了 actionId 的父分类才需要选子分类记账
            Type currentType = typeRepository.findById(flowAddRequestDto.getTypeId()).orElse(null);
            if (currentType != null && currentType.getActionId() != null) {
                throw new BusinessException(ErrorCode.TYPE_HAS_CHILDREN, "该分类有子分类，请选择子分类记账");
            }
        }

        String log = "新增flow\n"+"金额： "+ flowAddRequestDto.getMoney()+"";
        LogUtils.log_print(log);
        Flow flow = setNewFlow(flowAddRequestDto);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd hh:mm:ss");
        String createDate = sdf.format(new Date());
        flow.setFCreateDate(createDate);
        BeanUtils.copyProperties(flowAddRequestDto, flow);
        flowDao.addFlow(flow);

        // 保存图片关联
        if (flowAddRequestDto.getImages() != null && !flowAddRequestDto.getImages().isEmpty()) {
            imageService.saveFlowImages(flow.getId(), flowAddRequestDto.getImages());
        }

        return flow.getId();
    }

    private Flow setNewFlow(FlowAddRequestDto flowAddRequestDto) throws Exception {
        Action action = actionService.getAction(flowAddRequestDto.getActionId());
        Account account = accountService.getOriginAccountById(flowAddRequestDto.getAccountId() );
        Account toAccount = null;
        BigDecimal flowMoney = new BigDecimal(flowAddRequestDto.getMoney());
        BigDecimal accountMoney = new BigDecimal(account.getMoney());
        switch (action.getHandle()) {
            case ContentValues.ACTION_ADD:
                account = handleAccount(ContentValues.ACTION_ADD, flowAddRequestDto.getMoney(), account, action.isExempt());
                break;
            case ContentValues.ACTION_SUB:
                // v2.6.0: 注释余额检查，允许账户余额为负数
                // 场景：信用卡等负债账户，消费后余额为负表示欠款
                // if (accountMoney.compareTo(flowMoney) < 0) {
                //     throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE, "减少金额不允许大于账户金额");
                // }
                account = handleAccount(ContentValues.ACTION_SUB, flowAddRequestDto.getMoney(), account, action.isExempt());
                break;
            case ContentValues.ACTION_INNER:
                // v2.6.0: 注释余额检查，允许账户余额为负数
                // 场景：支持从负债账户转账（如信用卡还款：银行卡 → 信用卡）
                // if (accountMoney.compareTo(flowMoney) < 0) {
                //     throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE, "减少金额不允许大于账户金额");
                // }
                toAccount = accountService.getOriginAccountById(flowAddRequestDto.getAccountToId());
                // v2.6.0: 根据 exemptMode 决定哪个账户 exempt
                // 0=都不exempt，1=转出exempt，2=转入exempt，3=都exempt
                int exemptMode = action.getExemptMode() != null ? action.getExemptMode() : 0;
                boolean toAccountExempt = (exemptMode == 2 || exemptMode == 3);
                boolean fromAccountExempt = (exemptMode == 1 || exemptMode == 3);
                toAccount = handleAccount(ContentValues.ACTION_ADD, flowAddRequestDto.getMoney(), toAccount, toAccountExempt);
                accountService.updateOriginAccount(toAccount);
                account = handleAccount(ContentValues.ACTION_SUB, flowAddRequestDto.getMoney(), account, fromAccountExempt);
                break;
        }
        accountService.updateOriginAccount(account);

        Flow flow = new Flow();
        flow.setExempt(action.isExempt());
        BeanUtils.copyProperties(flowAddRequestDto, flow);
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
    public int doUpdateFlow(int id, FlowAddRequestDto flowAddRequestDto) throws Exception {
        // 格式化金额，确保只有2位小数
        flowAddRequestDto.setMoney(MoneyUtils.formatMoney(flowAddRequestDto.getMoney()));

        // 校验分类：有子分类且定义了actionId的父分类不允许直接记账
        List<Type> subTypes = typeRepository.findByParent(flowAddRequestDto.getTypeId());
        if (subTypes != null && !subTypes.isEmpty()) {
            // v2.6.0: 只有定义了 actionId 的父分类才需要选子分类记账
            Type currentType = typeRepository.findById(flowAddRequestDto.getTypeId()).orElse(null);
            if (currentType != null && currentType.getActionId() != null) {
                throw new BusinessException(ErrorCode.TYPE_HAS_CHILDREN, "该分类有子分类，请选择子分类记账");
            }
        }

        // 处理from字段：如果没有传入from字段，则置空
        if (flowAddRequestDto.getFrom() == null) {
            flowAddRequestDto.setFrom("");
        }

        String log = "更新flow\n"+"id: "+id+"\n金额： "+ flowAddRequestDto.getMoney()+"\n原操作： ";
        Flow lastFlow = flowDao.queryFlowById(id).get(0);
        Action lastAction = actionService.getAction(lastFlow.getActionId());
        Account lastAccount = accountService.getOriginAccountById(lastFlow.getAccountId() );
        // v2.5.1: 使用 lastFlow.isExempt() 而非 lastAction.isExempt()
        // 避免 Action 配置变更后导致还原操作使用错误的 exempt 状态
        boolean lastExempt = lastFlow.isExempt();
        switch (lastAction.getHandle()) {
            case ContentValues.ACTION_ADD:
                log = log+"金额增加\n";
                lastAccount = handleAccount(ContentValues.ACTION_SUB, lastFlow.getMoney(), lastAccount, lastExempt);
                break;
            case ContentValues.ACTION_SUB:
                log = log+"金额减少\n";
                lastAccount = handleAccount(ContentValues.ACTION_ADD, lastFlow.getMoney(), lastAccount, lastExempt);
                break;
            case ContentValues.ACTION_INNER:
                log = log+"内部转账\n";
                Account lastToAccount = accountService.getOriginAccountById(lastFlow.getAccountToId());
                // v2.6.0: 根据 exemptMode 还原内部转账
                int lastExemptMode = lastAction.getExemptMode() != null ? lastAction.getExemptMode() : 0;
                boolean lastToAccountExempt = (lastExemptMode == 2 || lastExemptMode == 3);
                boolean lastFromAccountExempt = (lastExemptMode == 1 || lastExemptMode == 3);
                lastToAccount = handleAccount(ContentValues.ACTION_SUB, lastFlow.getMoney(), lastToAccount, lastToAccountExempt);
                accountService.updateOriginAccount(lastToAccount);
                lastAccount = handleAccount(ContentValues.ACTION_ADD, lastFlow.getMoney(), lastAccount, lastFromAccountExempt);
                break;
        }
        LogUtils.log_print(log);
        accountService.updateOriginAccount(lastAccount);
        Flow flow = setNewFlow(flowAddRequestDto);
        flow.setId(id);
        BeanUtils.copyProperties(flowAddRequestDto, flow);
        flowDao.updateFlow(flow);

        // 更新图片关联（先删后加）
        imageService.deleteFlowImages(id);
        if (flowAddRequestDto.getImages() != null && !flowAddRequestDto.getImages().isEmpty()) {
            imageService.saveFlowImages(id, flowAddRequestDto.getImages());
        }

        return id;
    }

    private Account handleAccount(int handle, String money, Account account, boolean isExempt) {
        String log = "账户操作日志\n"+"账户名称： "+account.getAName()+"\n原始金额： "+account.getMoney()+"\n操作金额： "+money+"\n当前操作： ";
        BigDecimal flowMoney = new BigDecimal(money);
        BigDecimal accountMoney = new BigDecimal(account.getMoney());
        // v2.5.1: exemptMoney 可能为空字符串或 null，需要处理，避免 BigDecimal 解析异常
        String exemptMoneyStr = account.getExemptMoney();
        if (exemptMoneyStr == null || exemptMoneyStr.isEmpty()) {
            exemptMoneyStr = "0";
        }
        BigDecimal accountExemptMoney = isExempt ? new BigDecimal(exemptMoneyStr) : null;
        switch (handle) {
            case ContentValues.ACTION_ADD:
                log=log+"+\n";
                accountMoney = accountMoney.add(flowMoney);
                if (isExempt) {
                    accountExemptMoney = accountExemptMoney.add(flowMoney);
                    // v2.5.1: 添加精度控制，与 money 字段保持一致
                    account.setExemptMoney(accountExemptMoney.setScale(2, java.math.RoundingMode.HALF_UP).toString());
                }
                break;
            case ContentValues.ACTION_SUB:
                log=log+"-\n";
                accountMoney = accountMoney.subtract(flowMoney);
                if (isExempt) {
                    accountExemptMoney = accountExemptMoney.subtract(flowMoney);
                    // v2.5.1: 添加精度控制，与 money 字段保持一致
                    account.setExemptMoney(accountExemptMoney.setScale(2, java.math.RoundingMode.HALF_UP).toString());
                }
                break;
        }
        account.setMoney(accountMoney.setScale(2, java.math.RoundingMode.HALF_UP).toString());
        log=log+"结转金额： "+account.getMoney();
        LogUtils.log_print(log);
        return account;
    }

    @Transactional(rollbackFor = Exception.class)
    public FlowSingleResponseDto doQueryFlow(int id) {
        String log = "查询flow\n"+"id： "+id+"";
        List<Flow> flows = flowDao.queryFlowById(id);
        if (flows == null || flows.size() == 0) {
            return null;
        }
        FlowSingleResponseDto toClientBean = new FlowSingleResponseDto();
        Flow flow = flows.get(0);
        BeanUtils.copyProperties(flow, toClientBean);
        Account account = accountService.getOriginAccountById(flow.getAccountId() );
        Action action = actionService.getAction(flow.getActionId());
        Type type = typeService.queryTypeSingle(flow.getTypeId());
        TypeListResponseDto typeListResponseDto = new TypeListResponseDto();
        typeListResponseDto.convertToDto(type);
        if (type.getParent() != -1) {
            Type parentType = typeService.queryTypeSingle(type.getParent());
            typeListResponseDto.setTName(parentType.getTName() + "——" + type.getTName());
        }
        if (action.getHandle() == ContentValues.ACTION_INNER) {
            Account toAccount = accountService.getOriginAccountById(flow.getAccountToId());
            toClientBean.setAccountTo(toAccount);
        }
        toClientBean.setType(typeListResponseDto);
        toClientBean.setAccount(account);
        toClientBean.setAction(action);
        
        // 获取图片列表
        List<FlowImage> flowImages = imageService.getFlowImages(id);
        if (flowImages != null && !flowImages.isEmpty()) {
            List<String> imageNames = new ArrayList<>();
            for (FlowImage flowImage : flowImages) {
                imageNames.add(flowImage.getImageName());
            }
            toClientBean.setImages(imageNames);
        }
        
        LogUtils.log_print(log);
        LogUtils.log_json(toClientBean);
        return toClientBean;
    }

    @Transactional(rollbackFor = Exception.class)
    public void doDeleteFlow(int id) throws Exception {
        String log = "删除flow\n"+"id： "+id+"";
        LogUtils.log_print(log);
        Flow flow = flowDao.queryFlowById(id).get(0);
        Action lastAction = actionService.getAction(flow.getActionId());
        Account lastAccount = accountService.getOriginAccountById(flow.getAccountId() );
        // v2.5.1: 使用 flow.isExempt() 而非 lastAction.isExempt()
        // 避免 Action 配置变更后导致还原操作使用错误的 exempt 状态
        boolean flowExempt = flow.isExempt();
        switch (lastAction.getHandle()) {
            case ContentValues.ACTION_ADD:
                lastAccount = handleAccount(ContentValues.ACTION_SUB, flow.getMoney(), lastAccount, flowExempt);
                break;
            case ContentValues.ACTION_SUB:
                lastAccount = handleAccount(ContentValues.ACTION_ADD, flow.getMoney(), lastAccount, flowExempt);
                break;
            case ContentValues.ACTION_INNER:
                Account lastToAccount = accountService.getOriginAccountById(flow.getAccountToId());
                // v2.6.0: 根据 exemptMode 还原内部转账
                int delExemptMode = lastAction.getExemptMode() != null ? lastAction.getExemptMode() : 0;
                boolean delToAccountExempt = (delExemptMode == 2 || delExemptMode == 3);
                boolean delFromAccountExempt = (delExemptMode == 1 || delExemptMode == 3);
                lastToAccount = handleAccount(ContentValues.ACTION_SUB, flow.getMoney(), lastToAccount, delToAccountExempt);
                accountService.updateOriginAccount(lastToAccount);
                lastAccount = handleAccount(ContentValues.ACTION_ADD, flow.getMoney(), lastAccount, delFromAccountExempt);
                break;
        }

        accountService.updateOriginAccount(lastAccount);
        flowDao.deleteFlowById(id);
    }

    @Transactional(rollbackFor = Exception.class)
    public FlowListDto doGetMainBean(int handle, int order, String date) {
        String monthStr = date.substring(0, 7) + "%";
        FlowListDto flowListDto = new FlowListDto();
        SimpleDateFormat sdf1 = new SimpleDateFormat("yyyyMMdd_HHmm");
        String time = sdf1.format(new Date());
        log.info("time:  "+time+"   date: " + monthStr + "  handle: " + handle);
        List<Map<String, Object>> maps = flowDao.getFlowByMain(handle, order, monthStr) ;
        List<FlowListDto.FlowListSingleDto> flows = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        BigDecimal moneyIn = new BigDecimal("0");
        BigDecimal moneyOut = new BigDecimal("0");
        for (Map<String, Object> map : maps) {
            FlowListDto.FlowListSingleDto flow = new FlowListDto.FlowListSingleDto();
            flow.setId((Integer) map.get("id"));
            flow.setMoney((String) map.get("money"));
            flow.setExempt((Boolean) map.get("exempt"));
            flow.setCollect((Boolean) map.get("collect"));
            flow.setHandle((Integer) map.get("handle"));
            flow.setHName((String) map.get("h_name"));
            Date fDate = (Date) map.get("f_date");

            flow.setFDate(sdf.format(fDate));
            flow.setAName((String) map.get("a_name"));
            flow.setNote((String) map.get("note"));
            flow.setToAName((String) map.get("t_a_name"));
            flow.setFrom((String) map.get("from_source"));
            
            // 查询是否有图片
            Integer flowId = (Integer) map.get("id");
            List<FlowImage> images = imageService.getFlowImages(flowId);
            flow.setHasImages(images != null && !images.isEmpty());

            if (map.get("p_t_name") != null) {
                flow.setTName(map.get("p_t_name") + "/" + map.get("t_name"));
            } else {
                flow.setTName((String) map.get("t_name"));
            }
            flows.add(flow);
            if (flow.getHandle() == 1) {
                moneyOut = moneyOut.add(new BigDecimal(flow.getMoney()));
            } else if (flow.getHandle() == 0) {
                moneyIn = moneyIn.add(new BigDecimal(flow.getMoney()));
            }
        }

        flowListDto.setTotalIn(moneyIn.toString());
        flowListDto.setTotalOut(moneyOut.toString());
        flowListDto.setFlows(flows);
        return flowListDto;
    }

}
