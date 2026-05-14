package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dao.jpa.ScheduledFlowLogRepository;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.dto.ScheduledFlowLogResponseDto;
import com.deepblue.yd_jz.dto.ScheduledFlowPreviewDto;
import com.deepblue.yd_jz.dto.ScheduledFlowRuleRequestDto;
import com.deepblue.yd_jz.dto.ScheduledFlowRuleResponseDto;
import com.deepblue.yd_jz.entity.ScheduledFlowLog;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.service.ScheduledFlowRuleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

// v2.7.0: 定时记账 REST API
@Slf4j
@RestController
@Tag(name = "定时记账")
@RequestMapping("/scheduledFlow")
public class ScheduledFlowController {

    @Autowired
    private ScheduledFlowRuleService ruleService;

    @Autowired
    private ScheduledFlowLogRepository logRepo;

    // ════════════════════════ 规则 CRUD ════════════════════════

    @Operation(summary = "创建定时规则")
    @PostMapping("/rule")
    public BaseDto<ScheduledFlowRuleResponseDto> createRule(@RequestBody ScheduledFlowRuleRequestDto dto) {
        ScheduledFlowRule saved = ruleService.createRule(dto.toEntity());
        BaseDto<ScheduledFlowRuleResponseDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowRuleResponseDto.fromEntity(ruleService.getRule(saved.getId())));
        return res;
    }

    @Operation(summary = "修改定时规则")
    @PutMapping("/rule/{id}")
    public BaseDto<ScheduledFlowRuleResponseDto> updateRule(
            @PathVariable Integer id, @RequestBody ScheduledFlowRuleRequestDto dto) {
        ruleService.updateRule(id, dto.toEntity());
        BaseDto<ScheduledFlowRuleResponseDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowRuleResponseDto.fromEntity(ruleService.getRule(id)));
        return res;
    }

    @Operation(summary = "删除定时规则（级联删执行日志、未读通知）")
    @DeleteMapping("/rule/{id}")
    public BaseDto deleteRule(@PathVariable Integer id) {
        ruleService.deleteRule(id);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "获取定时规则详情")
    @GetMapping("/rule/{id}")
    public BaseDto<ScheduledFlowRuleResponseDto> getRule(@PathVariable Integer id) {
        BaseDto<ScheduledFlowRuleResponseDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowRuleResponseDto.fromEntity(ruleService.getRule(id)));
        return res;
    }

    @Operation(summary = "获取全部定时规则列表")
    @GetMapping("/rule/list")
    public BaseDto<List<ScheduledFlowRuleResponseDto>> listRules() {
        List<ScheduledFlowRuleResponseDto> list = ruleService.listRules().stream()
                .map(ScheduledFlowRuleResponseDto::fromEntity)
                .collect(Collectors.toList());
        BaseDto<List<ScheduledFlowRuleResponseDto>> res = BaseDto.setSuccessBean();
        res.setData(list);
        return res;
    }

    // ════════════════════════ 状态操作 ════════════════════════

    @Operation(summary = "启动（用户点开始）—— 暂停/完成/失效 → 开始")
    @PostMapping("/rule/{id}/start")
    public BaseDto<ScheduledFlowRuleResponseDto> startRule(@PathVariable Integer id) {
        ruleService.startRule(id);
        BaseDto<ScheduledFlowRuleResponseDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowRuleResponseDto.fromEntity(ruleService.getRule(id)));
        return res;
    }

    @Operation(summary = "暂停（用户点暂停）—— 开始 → 暂停")
    @PostMapping("/rule/{id}/pause")
    public BaseDto<ScheduledFlowRuleResponseDto> pauseRule(@PathVariable Integer id) {
        ruleService.pauseRule(id);
        BaseDto<ScheduledFlowRuleResponseDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowRuleResponseDto.fromEntity(ruleService.getRule(id)));
        return res;
    }

    // ════════════════════════ 预览 ════════════════════════

    @Operation(summary = "预览未来一轮执行日（每月=下月 / 每年=下年 / 每日每周=空）")
    @GetMapping("/rule/{id}/preview")
    public BaseDto<ScheduledFlowPreviewDto> preview(@PathVariable Integer id) {
        BaseDto<ScheduledFlowPreviewDto> res = BaseDto.setSuccessBean();
        res.setData(ScheduledFlowPreviewDto.fromLocalDates(ruleService.previewNextCycle(id)));
        return res;
    }

    // ════════════════════════ 执行日志 ════════════════════════

    @Operation(summary = "按规则查执行日志（倒序分页）")
    @GetMapping("/log")
    public BaseDto<List<ScheduledFlowLogResponseDto>> listLogs(
            @RequestParam(required = false) Integer ruleId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<ScheduledFlowLog> p = (ruleId == null)
                ? logRepo.findAllByOrderByExecuteTimeDesc(pageable)
                : logRepo.findByRuleIdOrderByExecuteTimeDesc(ruleId, pageable);
        List<ScheduledFlowLogResponseDto> list = p.getContent().stream()
                .map(ScheduledFlowLogResponseDto::fromEntity)
                .collect(Collectors.toList());
        BaseDto<List<ScheduledFlowLogResponseDto>> res = BaseDto.setSuccessBean();
        res.setData(list);
        return res;
    }

    @Operation(summary = "删除单条执行日志")
    @DeleteMapping("/log/{id}")
    public BaseDto deleteLog(@PathVariable Integer id) {
        ruleService.deleteLog(id);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "按规则清空所有执行日志")
    @DeleteMapping("/log")
    public BaseDto clearLogsByRule(@RequestParam Integer ruleId) {
        ruleService.clearLogsByRule(ruleId);
        return BaseDto.setSuccessBean();
    }

    // v2.7.0 (config-ui): 全局提醒配置已迁移到 /system/config/scheduledFlow（GET / PUT），统一系统设置入口
}
