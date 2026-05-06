package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.ScheduledFlowRuleStateMachine.Event;
import org.junit.jupiter.api.Test;

import static com.deepblue.yd_jz.utils.ScheduledFlowConst.*;
import static org.junit.jupiter.api.Assertions.*;

// v2.7.0: 状态机单测，覆盖 5 种事件 × 合法/非法前置状态
// dev-log §十一.3 后 SYS_INVALIDATE 放宽为"非 INVALID 均可"
class ScheduledFlowRuleStateMachineTest {

    // ─────────────────────────────────────────
    // 合法转移：成功改 status
    // ─────────────────────────────────────────
    @Test
    void userStart_fromPaused_toRunning() {
        assertTransit(STATUS_PAUSED, Event.USER_START, STATUS_RUNNING);
    }

    @Test
    void userStart_fromCompleted_toRunning() {
        assertTransit(STATUS_COMPLETED, Event.USER_START, STATUS_RUNNING);
    }

    @Test
    void userStart_fromInvalid_toRunning() {
        assertTransit(STATUS_INVALID, Event.USER_START, STATUS_RUNNING);
    }

    @Test
    void userPause_fromRunning_toPaused() {
        assertTransit(STATUS_RUNNING, Event.USER_PAUSE, STATUS_PAUSED);
    }

    @Test
    void sysBecomeRunning_fromNotStart_toRunning() {
        assertTransit(STATUS_NOT_START, Event.SYS_BECOME_RUNNING, STATUS_RUNNING);
    }

    @Test
    void sysComplete_fromRunning_toCompleted() {
        assertTransit(STATUS_RUNNING, Event.SYS_COMPLETE, STATUS_COMPLETED);
    }

    // SYS_INVALIDATE 前置：任何非 INVALID 状态都允许
    @Test
    void sysInvalidate_fromNotStart_toInvalid() {
        assertTransit(STATUS_NOT_START, Event.SYS_INVALIDATE, STATUS_INVALID);
    }

    @Test
    void sysInvalidate_fromRunning_toInvalid() {
        assertTransit(STATUS_RUNNING, Event.SYS_INVALIDATE, STATUS_INVALID);
    }

    @Test
    void sysInvalidate_fromPaused_toInvalid() {
        assertTransit(STATUS_PAUSED, Event.SYS_INVALIDATE, STATUS_INVALID);
    }

    @Test
    void sysInvalidate_fromCompleted_toInvalid() {
        assertTransit(STATUS_COMPLETED, Event.SYS_INVALIDATE, STATUS_INVALID);
    }

    // ─────────────────────────────────────────
    // 非法转移：抛 ILLEGAL_STATE_TRANSITION，不改 status
    // ─────────────────────────────────────────
    @Test
    void userStart_fromNotStart_throws() {
        assertIllegal(STATUS_NOT_START, Event.USER_START);
    }

    @Test
    void userStart_fromRunning_throws() {
        assertIllegal(STATUS_RUNNING, Event.USER_START);
    }

    @Test
    void userPause_fromNotStart_throws() {
        assertIllegal(STATUS_NOT_START, Event.USER_PAUSE);
    }

    @Test
    void userPause_fromPaused_throws() {
        assertIllegal(STATUS_PAUSED, Event.USER_PAUSE);
    }

    @Test
    void userPause_fromCompleted_throws() {
        assertIllegal(STATUS_COMPLETED, Event.USER_PAUSE);
    }

    @Test
    void userPause_fromInvalid_throws() {
        assertIllegal(STATUS_INVALID, Event.USER_PAUSE);
    }

    @Test
    void sysBecomeRunning_fromRunning_throws() {
        assertIllegal(STATUS_RUNNING, Event.SYS_BECOME_RUNNING);
    }

    @Test
    void sysBecomeRunning_fromPaused_throws() {
        // 避免歧义：暂停 → 开始必须走 USER_START，而不是系统自动
        assertIllegal(STATUS_PAUSED, Event.SYS_BECOME_RUNNING);
    }

    @Test
    void sysComplete_fromNotStart_throws() {
        assertIllegal(STATUS_NOT_START, Event.SYS_COMPLETE);
    }

    @Test
    void sysComplete_fromInvalid_throws() {
        assertIllegal(STATUS_INVALID, Event.SYS_COMPLETE);
    }

    // INVALID → INVALID 是唯一对 SYS_INVALIDATE 非法的前置（已经失效不用再失效）
    @Test
    void sysInvalidate_fromInvalid_throws() {
        assertIllegal(STATUS_INVALID, Event.SYS_INVALIDATE);
    }

    // ─────────────────────────────────────────
    // 非法转移的错误码是 ILLEGAL_STATE_TRANSITION
    // ─────────────────────────────────────────
    @Test
    void illegalTransition_raisesCorrectErrorCode() {
        ScheduledFlowRule rule = ruleWith(STATUS_COMPLETED);
        BusinessException ex = assertThrows(BusinessException.class,
                () -> ScheduledFlowRuleStateMachine.transit(rule, Event.USER_PAUSE));
        assertEquals(ErrorCode.ILLEGAL_STATE_TRANSITION.getCode(), ex.getCode());
    }

    // ─────────────────────────────────────────
    // 非法转移时，原 status 不被改动（副作用安全）
    // ─────────────────────────────────────────
    @Test
    void illegalTransition_doesNotMutateRule() {
        ScheduledFlowRule rule = ruleWith(STATUS_COMPLETED);
        assertThrows(BusinessException.class,
                () -> ScheduledFlowRuleStateMachine.transit(rule, Event.USER_PAUSE));
        assertEquals(STATUS_COMPLETED, rule.getStatus(), "非法转移不应改动原 status");
    }

    // ─────────────────────────────────────────
    // helper
    // ─────────────────────────────────────────
    private static ScheduledFlowRule ruleWith(int status) {
        ScheduledFlowRule r = new ScheduledFlowRule();
        r.setStatus(status);
        return r;
    }

    private static void assertTransit(int from, Event event, int expectedTo) {
        ScheduledFlowRule rule = ruleWith(from);
        ScheduledFlowRuleStateMachine.transit(rule, event);
        assertEquals(expectedTo, rule.getStatus());
    }

    private static void assertIllegal(int from, Event event) {
        ScheduledFlowRule rule = ruleWith(from);
        assertThrows(BusinessException.class,
                () -> ScheduledFlowRuleStateMachine.transit(rule, event));
    }
}
