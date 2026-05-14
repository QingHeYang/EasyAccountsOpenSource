package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Date;

// v2.7.0 (auto-excel): 自动月度 Excel 业务编排
//
// 核心入口 runOnce()：
//   1. 算目标月（target=LAST_MONTH → 上月；CURRENT_MONTH → 当月）
//   2. 查当月流水数
//   3. 分支：
//      - count == 0：站内通知 "本月无流水，已跳过" + 邮件（无附件，如 send_email）
//      - count > 0：生成 Excel + 站内通知 + 邮件（有附件，如 send_email）
//      - 异常：站内通知失败原因，不重试不发邮件
//   4. 写 last_run_date 仅作展示
@Slf4j
@Service
public class AutoExcelExecuteService {

    private static final DateTimeFormatter YYYY_MM = DateTimeFormatter.ofPattern("yyyy-MM");

    @Autowired
    private AutoExcelConfigService configService;

    @Autowired
    private ExcelService excelService;

    @Autowired
    private MailService mailService;

    @Autowired
    private UserNoticeService noticeService;

    /**
     * 执行一次自动月度 Excel 生成。
     * 由 AutoExcelExecuteTask 在 cron 触发时调用，也可由 Controller 手动调用做测试。
     * 不抛异常（异常都吃下去转站内通知），保证调度链路不会因业务异常崩溃。
     *
     * @Transactional 必要：方法内 JPA（AppConfig/UserNotice 读写）+ MyBatis（FlowDao 查询）混用，
     * 不开事务会让 JPA OSIV 抢的连接和 MyBatis 申请的连接不共享，触发 Hikari 池等待超时
     */
    @Transactional(rollbackFor = Exception.class)
    public void runOnce() {
        LocalDate today = LocalDate.now();
        String target = configService.getTarget();
        YearMonth targetYm = AutoExcelConfigService.computeTargetYearMonth(today, target);
        String yearMonth = targetYm.format(YYYY_MM);

        log.info("auto_excel runOnce: today={}, target={}, yearMonth={}", today, target, yearMonth);

        try {
            int count = excelService.countMonthFlows(yearMonth);

            if (count == 0) {
                handleNoFlow(yearMonth);
            } else {
                handleGenerate(yearMonth, count);
            }
        } catch (Exception e) {
            log.error("auto_excel runOnce 失败 [{}]: {}", yearMonth, e.getMessage(), e);
            handleFailure(yearMonth, e.getMessage());
        } finally {
            configService.setLastRunDate(today);  // 仅展示用，无论成败都记
            // 清掉今天对应的"提前提醒"通知，避免通知列表里"3 天后将生成"和"已生成"并排
            // 防重时这些提醒的 relatedRunDate 写的是 cron 触发日 = today（cron 触发时 today=dom 那天）
            // 手动 runNow 时 today 通常 != cron 触发日，删 today 不会误删未来的提醒
            Date todayAsDate = Date.from(today.atStartOfDay(ZoneId.systemDefault()).toInstant());
            try {
                noticeService.deleteByTypeAndRunDate(
                        ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_REMIND, todayAsDate);
            } catch (Exception ignore) {
                log.warn("清理 auto_excel 提前提醒通知失败（不影响主流程）");
            }
        }
    }

    // ── 分支处理 ─────────────────────────────────────────

    private void handleNoFlow(String yearMonth) {
        log.info("auto_excel: {} 无流水，跳过生成", yearMonth);

        String title = "自动生成账单：" + yearMonth + " 无流水";
        String content = "您的 " + yearMonth + " 月账单 Excel 自动生成已跳过，因当月没有任何流水记录。\n" +
                "如这与您的实际情况不符，请检查是否漏记或晚记了流水。";
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_NO_FLOW,
                title, content, null, null);

        if (configService.isSendEmail()) {
            mailService.sendAutoExcelNoFlow(yearMonth);
        }
    }

    private void handleGenerate(String yearMonth, int count) {
        log.info("auto_excel: {} 共 {} 条流水，开始生成 Excel", yearMonth, count);

        File excel = excelService.makeMonthExcelFile(yearMonth);
        if (excel == null) {
            handleFailure(yearMonth, "Excel 文件生成失败（excelService 返回 null）");
            return;
        }

        String title = "自动生成账单：" + yearMonth + " 已生成";
        String content = "您的 " + yearMonth + " 月账单 Excel 已自动生成。\n" +
                "  文件名：" + excel.getName() + "\n" +
                "  流水条数：" + count;
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_GENERATED,
                title, content, null, null);

        if (configService.isSendEmail()) {
            mailService.sendMonthExcel(excel, yearMonth);
        }
    }

    private void handleFailure(String yearMonth, String reason) {
        log.warn("auto_excel: {} 生成失败 reason={}", yearMonth, reason);

        String title = "自动生成账单失败：" + yearMonth;
        String content = "您的 " + yearMonth + " 月账单 Excel 自动生成失败。\n" +
                "  失败原因：" + (reason == null ? "未知" : reason) + "\n" +
                "请稍后在前端手动触发生成，或检查服务器日志。";
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_FAILED,
                title, content, null, null);
        // 失败不发邮件（按产品规则）
    }
}
