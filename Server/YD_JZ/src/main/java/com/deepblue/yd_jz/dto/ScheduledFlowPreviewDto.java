package com.deepblue.yd_jz.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

// v2.7.0: 未来一轮执行日预览（每月=下月 / 每年=下年 / 每日/每周=空）
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScheduledFlowPreviewDto {
    private List<String> runDates;  // yyyy-MM-dd

    public static ScheduledFlowPreviewDto fromLocalDates(List<LocalDate> list) {
        return new ScheduledFlowPreviewDto(
                list.stream().map(LocalDate::toString).collect(Collectors.toList())
        );
    }
}
