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
}
