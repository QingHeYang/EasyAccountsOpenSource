package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.event.AutoExcelConfigChangedEvent;
import com.deepblue.yd_jz.service.AutoExcelConfigService;
import com.deepblue.yd_jz.service.AutoExcelExecuteService;
import com.deepblue.yd_jz.utils.CronBuilder;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.support.CronTrigger;
import org.springframework.stereotype.Component;

import java.util.concurrent.ScheduledFuture;

// v2.7.0 (auto-excel): 自动月度 Excel 调度任务
//
// 与 SQLBackUpTask 同款 Trigger 模式（Phase 4 已落地）：
//   1. @PostConstruct 时按当前配置首次安排
//   2. 监听 AutoExcelConfigChangedEvent 配置变更后取消旧任务、重排
//   3. enabled=false 时不安排任务
//   4. cron 由 CronBuilder.build("monthly", time, null, dayOfMonth) 现拼，每次 schedule() 现读
@Slf4j
@Component
public class AutoExcelExecuteTask {

    @Autowired
    private AutoExcelConfigService configService;

    @Autowired
    private AutoExcelExecuteService executeService;

    @Autowired
    private TaskScheduler taskScheduler;

    private ScheduledFuture<?> currentFuture;

    @PostConstruct
    public void init() {
        schedule();
    }

    @EventListener
    public synchronized void onConfigChanged(AutoExcelConfigChangedEvent event) {
        log.info("auto_excel config changed, rescheduling...");
        schedule();
    }

    private synchronized void schedule() {
        // 取消旧任务
        if (currentFuture != null && !currentFuture.isCancelled()) {
            currentFuture.cancel(false);
            currentFuture = null;
        }

        if (!configService.isEnabled()) {
            log.info("auto_excel 已关闭，未安排定时任务");
            return;
        }

        try {
            String cron = CronBuilder.build(
                    SystemConfigConst.FREQ_MONTHLY,
                    configService.getTime(),
                    null,
                    configService.getDayOfMonth());
            currentFuture = taskScheduler.schedule(executeService::runOnce, new CronTrigger(cron));
            log.info("auto_excel 已安排：cron={}, target={}, dayOfMonth={}, time={}",
                    cron, configService.getTarget(), configService.getDayOfMonth(), configService.getTime());
        } catch (Exception e) {
            log.error("安排 auto_excel 任务失败：{}", e.getMessage());
        }
    }
}
