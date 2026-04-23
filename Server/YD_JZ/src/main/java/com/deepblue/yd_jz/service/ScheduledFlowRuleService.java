package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.AccountRepository;
import com.deepblue.yd_jz.dao.jpa.ActionRepository;
import com.deepblue.yd_jz.dao.jpa.ScheduledFlowLogRepository;
import com.deepblue.yd_jz.dao.jpa.ScheduledFlowRuleRepository;
import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import com.deepblue.yd_jz.dao.jpa.UserNoticeRepository;
import com.deepblue.yd_jz.dto.FlowAddRequestDto;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.entity.ScheduledFlowLog;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.ContentValues;
import com.deepblue.yd_jz.utils.CycleCalculator;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import com.deepblue.yd_jz.utils.ScheduledFlowRuleStateMachine;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.regex.Pattern;

// v2.7.0: 定时记账规则业务逻辑层
@Slf4j
@Service
public class ScheduledFlowRuleService {

    private static final Pattern RUN_TIME_HHMM = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d$");
    private static final Pattern RUN_TIME_HHMMSS = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d:[0-5]\\d$");

    @Autowired
    private ScheduledFlowRuleRepository ruleRepo;

    @Autowired
    private ScheduledFlowLogRepository logRepo;

    @Autowired
    private UserNoticeRepository noticeRepo;

    @Autowired
    private AccountRepository accountRepo;

    @Autowired
    private TypeRepository typeRepo;

    @Autowired
    private ActionRepository actionRepo;

    @Autowired
    private FlowService flowService;

    // =====================================================================
    // CRUD
    // =====================================================================

    @Transactional(rollbackFor = Exception.class)
    public ScheduledFlowRule createRule(ScheduledFlowRule input) {
        validateFields(input);
        validateStartDateAfterToday(input.getStartDate());
        validateMasterDataUsable(input);

        input.setId(null);
        input.setRunTime(normalizeRunTime(input.getRunTime()));
        input.setStatus(ScheduledFlowConst.STATUS_NOT_START);
        input.setCreateTime(new Date());
        input.setPermanent(input.getEndDate() == null);
        input.setLastRunDate(null);
        input.setNextRunDate(toDate(computeFirstRunDate(input)));

        return ruleRepo.save(input);
    }

    @Transactional(rollbackFor = Exception.class)
    public ScheduledFlowRule updateRule(Integer id, ScheduledFlowRule patch) {
        ScheduledFlowRule existing = requireRule(id);
        validateFields(patch);
        validateMasterDataUsable(patch);

        // 仅在用户修改了 startDate 时，才校验"不早于明天"
        if (!toLocalDate(existing.getStartDate()).equals(toLocalDate(patch.getStartDate()))) {
            validateStartDateAfterToday(patch.getStartDate());
        }

        existing.setName(patch.getName());
        existing.setMoney(patch.getMoney());
        existing.setTypeId(patch.getTypeId());
        existing.setActionId(patch.getActionId());
        existing.setAccountId(patch.getAccountId());
        existing.setAccountToId(patch.getAccountToId());
        existing.setNote(patch.getNote());
        existing.setCycleType(patch.getCycleType());
        existing.setCycleDates(patch.getCycleDates());
        existing.setRunTime(normalizeRunTime(patch.getRunTime()));
        existing.setStartDate(patch.getStartDate());
        existing.setEndDate(patch.getEndDate());
        existing.setPermanent(patch.getEndDate() == null);
        existing.setReminderEnabled(patch.isReminderEnabled());
        existing.setEmailEnabled(patch.isEmailEnabled());

        // 字段改了就重算游标（不管当前状态；运行态等启动时也会重算）
        existing.setNextRunDate(toDate(computeNextRunDateAfter(existing, baselineForRecompute(existing))));

        return ruleRepo.save(existing);
    }

    @Transactional(rollbackFor = Exception.class)
    public void deleteRule(Integer id) {
        requireRule(id);
        logRepo.deleteByRuleId(id);
        noticeRepo.deleteByRelatedRuleId(id);
        ruleRepo.deleteById(id);
    }

    public ScheduledFlowRule getRule(Integer id) {
        return requireRule(id);
    }

    public List<ScheduledFlowRule> listRules() {
        return ruleRepo.findAll();
    }

    // =====================================================================
    // 状态操作
    // =====================================================================

    @Transactional(rollbackFor = Exception.class)
    public ScheduledFlowRule startRule(Integer id) {
        ScheduledFlowRule rule = requireRule(id);
        validateMasterDataUsable(rule);
        validateEndDateForStart(rule);

        // 启动时总是重算游标
        rule.setNextRunDate(toDate(computeNextRunDateAfter(rule, baselineForRecompute(rule))));

        ScheduledFlowRuleStateMachine.transit(rule, ScheduledFlowRuleStateMachine.Event.USER_START);
        return ruleRepo.save(rule);
    }

    @Transactional(rollbackFor = Exception.class)
    public ScheduledFlowRule pauseRule(Integer id) {
        ScheduledFlowRule rule = requireRule(id);
        ScheduledFlowRuleStateMachine.transit(rule, ScheduledFlowRuleStateMachine.Event.USER_PAUSE);
        return ruleRepo.save(rule);
    }

    // =====================================================================
    // 预览
    // =====================================================================

    public List<LocalDate> previewNextCycle(Integer id) {
        ScheduledFlowRule rule = requireRule(id);
        return CycleCalculator.previewNextCycle(
                rule.getCycleType(), rule.getCycleDates(), LocalDate.now());
    }

    // =====================================================================
    // 扫描器调用（P3）
    // =====================================================================

    /**
     * 生成本次流水：校验主数据 + 调 FlowService.doAddFlow + 删除对应事前提醒
     * 成功返回 flow.id；失败抛 BusinessException 或其它异常，由调用方分类处理
     */
    @Transactional(rollbackFor = Exception.class)
    public int executeRuleOrThrow(ScheduledFlowRule rule, LocalDate today) throws Exception {
        validateMasterDataUsable(rule);

        FlowAddRequestDto dto = new FlowAddRequestDto();
        dto.setMoney(rule.getMoney());
        dto.setfDate(today.toString());  // yyyy-MM-dd
        dto.setActionId(rule.getActionId());
        dto.setAccountId(rule.getAccountId());
        dto.setAccountToId(rule.getAccountToId() == null ? 0 : rule.getAccountToId());
        dto.setTypeId(rule.getTypeId());
        dto.setCollect(false);
        dto.setFrom(ScheduledFlowConst.FLOW_FROM_SCHEDULED);
        String note = rule.getNote() == null ? "" : rule.getNote();
        dto.setNote(note + ScheduledFlowConst.NOTE_TAG_SCHEDULED);

        int flowId = flowService.doAddFlow(dto);

        // 产品 §7.5 后补：执行过后自动删除对应的事前提醒
        noticeRepo.deleteByRelatedRuleIdAndRelatedRunDate(rule.getId(), toDate(today));

        return flowId;
    }

    @Transactional(rollbackFor = Exception.class)
    public void recordSuccess(Integer ruleId, Integer flowId) {
        ScheduledFlowLog entry = new ScheduledFlowLog();
        entry.setRuleId(ruleId);
        entry.setExecuteTime(new Date());
        entry.setSuccess(true);
        entry.setFlowId(flowId);
        logRepo.save(entry);
    }

    @Transactional(rollbackFor = Exception.class)
    public void recordFailure(Integer ruleId, Integer failCategory, String failReason) {
        ScheduledFlowLog entry = new ScheduledFlowLog();
        entry.setRuleId(ruleId);
        entry.setExecuteTime(new Date());
        entry.setSuccess(false);
        entry.setFailCategory(failCategory);
        entry.setFailReason(failReason == null ? "" : truncate(failReason, 500));
        logRepo.save(entry);
    }

    /**
     * 推进游标：算下次执行日 from=today
     * - markExecuted=true：执行成功路径，顺带更新 last_run_date = today
     * - markExecuted=false：错过/历史遗留路径，只推游标
     * 如果推后的 next_run_date 超过 end_date，触发 SYS_COMPLETE
     */
    @Transactional(rollbackFor = Exception.class)
    public void advanceCursor(ScheduledFlowRule rule, LocalDate today, boolean markExecuted) {
        if (markExecuted) {
            rule.setLastRunDate(toDate(today));
        }
        LocalDate next = CycleCalculator.nextRunDate(
                rule.getCycleType(), rule.getCycleDates(), today);
        if (rule.getEndDate() != null && next.isAfter(toLocalDate(rule.getEndDate()))) {
            rule.setNextRunDate(null);
            ScheduledFlowRuleStateMachine.transit(
                    rule, ScheduledFlowRuleStateMachine.Event.SYS_COMPLETE);
        } else {
            rule.setNextRunDate(toDate(next));
        }
        ruleRepo.save(rule);
    }

    /**
     * 扫描器发现 NOT_START 到达 start_date，自动切换为 RUNNING
     */
    @Transactional(rollbackFor = Exception.class)
    public void markRunning(ScheduledFlowRule rule) {
        ScheduledFlowRuleStateMachine.transit(
                rule, ScheduledFlowRuleStateMachine.Event.SYS_BECOME_RUNNING);
        ruleRepo.save(rule);
    }

    /**
     * 主数据类失败时标为失效
     */
    @Transactional(rollbackFor = Exception.class)
    public void markInvalid(ScheduledFlowRule rule) {
        ScheduledFlowRuleStateMachine.transit(
                rule, ScheduledFlowRuleStateMachine.Event.SYS_INVALIDATE);
        ruleRepo.save(rule);
    }

    private static String truncate(String s, int max) {
        return s.length() <= max ? s : s.substring(0, max);
    }

    // =====================================================================
    // 主数据事件挂钩（P4 AccountService / TypeService 停用路径直接调用）
    // 账户停用、分类停用或归档时，顺带把引用它们的 RUNNING 规则标为失效
    // =====================================================================

    @Transactional(rollbackFor = Exception.class)
    public void invalidateByAccount(Integer accountId) {
        List<ScheduledFlowRule> rules = ruleRepo.findActiveRulesByAccountId(
                ScheduledFlowConst.STATUS_RUNNING, accountId);
        for (ScheduledFlowRule rule : rules) {
            // 置空被停用账户的引用字段（主账户 / 转账目标账户 任一命中就置空）
            if (accountId.equals(rule.getAccountId())) {
                rule.setAccountId(null);
            }
            if (accountId.equals(rule.getAccountToId())) {
                rule.setAccountToId(null);
            }
            ScheduledFlowRuleStateMachine.transit(rule, ScheduledFlowRuleStateMachine.Event.SYS_INVALIDATE);
            ruleRepo.save(rule);
            log.info("rule {} invalidated, account {} cleared", rule.getId(), accountId);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void invalidateByType(Integer typeId) {
        List<ScheduledFlowRule> rules = ruleRepo.findActiveRulesByTypeId(
                ScheduledFlowConst.STATUS_RUNNING, typeId);
        for (ScheduledFlowRule rule : rules) {
            // 置空分类引用
            rule.setTypeId(null);
            ScheduledFlowRuleStateMachine.transit(rule, ScheduledFlowRuleStateMachine.Event.SYS_INVALIDATE);
            ruleRepo.save(rule);
            log.info("rule {} invalidated, type {} cleared", rule.getId(), typeId);
        }
    }

    // =====================================================================
    // 私有：校验
    // =====================================================================

    private ScheduledFlowRule requireRule(Integer id) {
        return ruleRepo.findById(id)
                .orElseThrow(() -> new BusinessException(ErrorCode.SCHEDULED_RULE_NOT_FOUND));
    }

    private void validateFields(ScheduledFlowRule rule) {
        if (rule.getName() == null || rule.getName().trim().isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_REQUIRED, "规则名称不能为空");
        }
        if (rule.getMoney() == null || rule.getMoney().trim().isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_REQUIRED, "金额不能为空");
        }
        if (rule.getTypeId() == null || rule.getActionId() == null || rule.getAccountId() == null) {
            throw new BusinessException(ErrorCode.PARAM_REQUIRED, "分类/收支/账户不能为空");
        }
        if (rule.getStartDate() == null) {
            throw new BusinessException(ErrorCode.PARAM_REQUIRED, "开始日期不能为空");
        }
        if (rule.getCycleType() == null
                || rule.getCycleType() < ScheduledFlowConst.CYCLE_DAILY
                || rule.getCycleType() > ScheduledFlowConst.CYCLE_YEARLY) {
            throw new BusinessException(ErrorCode.INVALID_CYCLE_CONFIG, "周期类型非法");
        }
        if (rule.getCycleType() != ScheduledFlowConst.CYCLE_DAILY
                && (rule.getCycleDates() == null || rule.getCycleDates().trim().isEmpty())) {
            throw new BusinessException(ErrorCode.INVALID_CYCLE_CONFIG, "周期内日期不能为空");
        }
        if (rule.getRunTime() == null || !isValidRunTime(rule.getRunTime())) {
            throw new BusinessException(ErrorCode.PARAM_FORMAT_ERROR, "执行时间格式错误，应为 HH:mm 或 HH:mm:ss");
        }
        if (rule.getEndDate() != null && rule.getEndDate().before(rule.getStartDate())) {
            throw new BusinessException(ErrorCode.INVALID_END_DATE);
        }
    }

    private void validateStartDateAfterToday(Date startDate) {
        if (!toLocalDate(startDate).isAfter(LocalDate.now())) {
            throw new BusinessException(ErrorCode.INVALID_START_DATE);
        }
    }

    private void validateEndDateForStart(ScheduledFlowRule rule) {
        if (rule.getEndDate() != null && toLocalDate(rule.getEndDate()).isBefore(LocalDate.now())) {
            throw new BusinessException(ErrorCode.RULE_EXPIRED);
        }
    }

    private void validateMasterDataUsable(ScheduledFlowRule rule) {
        Account account = accountRepo.findById(rule.getAccountId())
                .orElseThrow(() -> new BusinessException(ErrorCode.ACCOUNT_NOT_FOUND));
        if (Boolean.TRUE.equals(account.getDisable())) {
            throw new BusinessException(ErrorCode.ACCOUNT_DISABLED,
                    "账户「" + account.getAName() + "」已停用");
        }

        Type type = typeRepo.findById(rule.getTypeId())
                .orElseThrow(() -> new BusinessException(ErrorCode.TYPE_NOT_FOUND));
        if (type.isDisable()) {
            throw new BusinessException(ErrorCode.TYPE_DISABLED,
                    "分类「" + type.getTName() + "」已停用");
        }
        if (Boolean.TRUE.equals(type.getArchive())) {
            throw new BusinessException(ErrorCode.TYPE_ARCHIVED,
                    "分类「" + type.getTName() + "」已归档");
        }

        Action action = actionRepo.findById(rule.getActionId())
                .orElseThrow(() -> new BusinessException(ErrorCode.ACTION_NOT_FOUND));

        if (action.getHandle() == ContentValues.ACTION_INNER) {
            if (rule.getAccountToId() == null) {
                throw new BusinessException(ErrorCode.TRANSFER_ACCOUNT_REQUIRED);
            }
            if (rule.getAccountToId().equals(rule.getAccountId())) {
                throw new BusinessException(ErrorCode.PARAM_INVALID, "转账目标账户不能与主账户相同");
            }
            Account toAccount = accountRepo.findById(rule.getAccountToId())
                    .orElseThrow(() -> new BusinessException(ErrorCode.ACCOUNT_NOT_FOUND, "目标账户不存在"));
            if (Boolean.TRUE.equals(toAccount.getDisable())) {
                throw new BusinessException(ErrorCode.ACCOUNT_DISABLED,
                        "目标账户「" + toAccount.getAName() + "」已停用");
            }
        }
    }

    // =====================================================================
    // 私有：游标计算
    // =====================================================================

    /**
     * 创建时计算首次执行日：from = startDate - 1，保证第一次落在 startDate 或之后符合周期的第一天
     */
    private LocalDate computeFirstRunDate(ScheduledFlowRule rule) {
        LocalDate startDate = toLocalDate(rule.getStartDate());
        return CycleCalculator.nextRunDate(
                rule.getCycleType(), rule.getCycleDates(), startDate.minusDays(1));
    }

    /**
     * update / start 时重算游标的基准日期
     * - 如果 startDate 还在未来 → from = startDate - 1（首次会落在 startDate 或之后）
     * - 如果 startDate 已过    → from = 今天（next 会落在今天之后最近的符合周期日）
     */
    private LocalDate baselineForRecompute(ScheduledFlowRule rule) {
        LocalDate startDate = toLocalDate(rule.getStartDate());
        LocalDate today = LocalDate.now();
        return startDate.isAfter(today) ? startDate.minusDays(1) : today;
    }

    private LocalDate computeNextRunDateAfter(ScheduledFlowRule rule, LocalDate from) {
        return CycleCalculator.nextRunDate(rule.getCycleType(), rule.getCycleDates(), from);
    }

    // =====================================================================
    // 私有：工具
    // =====================================================================

    private static boolean isValidRunTime(String s) {
        String t = s.trim();
        return RUN_TIME_HHMM.matcher(t).matches() || RUN_TIME_HHMMSS.matcher(t).matches();
    }

    private static String normalizeRunTime(String input) {
        String t = input.trim();
        return RUN_TIME_HHMM.matcher(t).matches() ? t + ":00" : t;
    }

    private static LocalDate toLocalDate(Date date) {
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDate();
    }

    private static Date toDate(LocalDate localDate) {
        return Date.from(localDate.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
