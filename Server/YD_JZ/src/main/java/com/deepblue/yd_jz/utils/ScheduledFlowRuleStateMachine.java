package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;

// v2.7.0: 定时记账规则状态机
// 所有改 status 的路径必须走它，严禁 Service 直接 rule.setStatus(...)
//
// 合法转移：
//   USER_START           : 暂停/完成/失效 → 开始
//   USER_PAUSE           : 开始 → 暂停
//   SYS_BECOME_RUNNING   : 未开始 → 开始（到达 start_date 时系统自动）
//   SYS_COMPLETE         : 开始 → 完成（推进游标超过 end_date）
//   SYS_INVALIDATE       : 开始 → 失效（主数据失效事件驱动）
@Slf4j
public class ScheduledFlowRuleStateMachine {

    public enum Event {
        USER_START,
        USER_PAUSE,
        SYS_BECOME_RUNNING,
        SYS_COMPLETE,
        SYS_INVALIDATE
    }

    public static void transit(ScheduledFlowRule rule, Event event) {
        int from = rule.getStatus();
        int to = calcTarget(from, event);
        log.debug("state transit: ruleId={}, {} --{}--> {}", rule.getId(), from, event, to);
        rule.setStatus(to);
    }

    private static int calcTarget(int from, Event event) {
        switch (event) {
            case USER_START:
                if (from == ScheduledFlowConst.STATUS_PAUSED
                        || from == ScheduledFlowConst.STATUS_COMPLETED
                        || from == ScheduledFlowConst.STATUS_INVALID) {
                    return ScheduledFlowConst.STATUS_RUNNING;
                }
                break;
            case USER_PAUSE:
                if (from == ScheduledFlowConst.STATUS_RUNNING) {
                    return ScheduledFlowConst.STATUS_PAUSED;
                }
                break;
            case SYS_BECOME_RUNNING:
                if (from == ScheduledFlowConst.STATUS_NOT_START) {
                    return ScheduledFlowConst.STATUS_RUNNING;
                }
                break;
            case SYS_COMPLETE:
                if (from == ScheduledFlowConst.STATUS_RUNNING) {
                    return ScheduledFlowConst.STATUS_COMPLETED;
                }
                break;
            case SYS_INVALIDATE:
                // 产品 §5.3：账户/分类停用归档时，引用它的任何非失效规则都应进入失效
                if (from != ScheduledFlowConst.STATUS_INVALID) {
                    return ScheduledFlowConst.STATUS_INVALID;
                }
                break;
        }
        throw new BusinessException(ErrorCode.ILLEGAL_STATE_TRANSITION,
                "状态转移非法：from=" + from + ", event=" + event);
    }
}
