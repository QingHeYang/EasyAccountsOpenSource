package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.UserNotice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Date;
import java.util.List;

@Repository
public interface UserNoticeRepository extends JpaRepository<UserNotice, Integer> {

    // 通知列表（按已读过滤 + 按时间倒序）
    List<UserNotice> findByIsReadOrderByCreateTimeDesc(boolean isRead);

    List<UserNotice> findAllByOrderByCreateTimeDesc();

    // 防重复：查某规则某执行日是否已发过提醒
    UserNotice findByRelatedRuleIdAndRelatedRunDate(Integer relatedRuleId, Date relatedRunDate);

    // 执行后清理对应事前提醒（产品 §7.5 后补）
    void deleteByRelatedRuleIdAndRelatedRunDate(Integer relatedRuleId, Date relatedRunDate);

    // 规则删除时级联清未读通知
    void deleteByRelatedRuleId(Integer relatedRuleId);

    // v2.7.0 (auto-excel): 按 type + runDate 防重；auto_excel 单条全局规则无 ruleId，用 type 作分类键
    UserNotice findFirstByTypeAndRelatedRunDate(Integer type, Date relatedRunDate);

    // v2.7.0 (auto-excel): 事后清理 —— runOnce 执行成功后清掉那一天的旧"提前提醒"通知，避免通知列表混乱
    void deleteByTypeAndRelatedRunDate(Integer type, Date relatedRunDate);
}
