package com.deepblue.yd_jz.event;

import org.springframework.context.ApplicationEvent;

// v2.7.0 (auto-excel): 自动月度 Excel 配置变更事件
// AutoExcelConfigService.update() 后发布；AutoExcelExecuteTask 监听后调 schedule() 重排
// 与 BackupConfigChangedEvent 同套路，事件解耦避免循环依赖
public class AutoExcelConfigChangedEvent extends ApplicationEvent {
    public AutoExcelConfigChangedEvent(Object source) {
        super(source);
    }
}
