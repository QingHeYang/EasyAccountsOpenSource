package com.deepblue.yd_jz.event;

import org.springframework.context.ApplicationEvent;

// v2.7.0 (config-ui): 备份配置变更事件
// BackupConfigService.update() 后发布；SQLBackUpTask 监听后调 reload() 重排调度
// 用事件解耦，避免 BackupConfigService 与 SQLBackUpTask 双向依赖
public class BackupConfigChangedEvent extends ApplicationEvent {
    public BackupConfigChangedEvent(Object source) {
        super(source);
    }
}
