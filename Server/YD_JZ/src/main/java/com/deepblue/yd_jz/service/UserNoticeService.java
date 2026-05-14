package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.UserNoticeRepository;
import com.deepblue.yd_jz.entity.UserNotice;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;

// v2.7.0: 用户信息通知服务
@Slf4j
@Service
public class UserNoticeService {

    @Autowired
    private UserNoticeRepository repo;

    @Transactional(rollbackFor = Exception.class)
    public UserNotice create(Integer type, String title, String content,
                             Integer relatedRuleId, Date relatedRunDate) {
        UserNotice n = new UserNotice();
        n.setType(type);
        n.setTitle(title);
        n.setContent(content);
        n.setRelatedRuleId(relatedRuleId);
        n.setRelatedRunDate(relatedRunDate);
        n.setRead(false);
        n.setCreateTime(new Date());
        return repo.save(n);
    }

    public List<UserNotice> listAll() {
        return repo.findAllByOrderByCreateTimeDesc();
    }

    public List<UserNotice> listByRead(boolean read) {
        return repo.findByIsReadOrderByCreateTimeDesc(read);
    }

    @Transactional(rollbackFor = Exception.class)
    public void markRead(Integer id) {
        UserNotice n = repo.findById(id)
                .orElseThrow(() -> new BusinessException(ErrorCode.NOTICE_NOT_FOUND));
        n.setRead(true);
        repo.save(n);
    }

    @Transactional(rollbackFor = Exception.class)
    public void markAllRead() {
        List<UserNotice> unread = repo.findByIsReadOrderByCreateTimeDesc(false);
        for (UserNotice n : unread) {
            n.setRead(true);
        }
        repo.saveAll(unread);
    }

    @Transactional(rollbackFor = Exception.class)
    public void delete(Integer id) {
        if (!repo.existsById(id)) {
            throw new BusinessException(ErrorCode.NOTICE_NOT_FOUND);
        }
        repo.deleteById(id);
    }

    /**
     * 防重复：查某规则在某执行日是否已经发过提醒
     */
    public boolean existsReminderFor(Integer ruleId, Date runDate) {
        return repo.findByRelatedRuleIdAndRelatedRunDate(ruleId, runDate) != null;
    }

    /**
     * 防重复（按 type + runDate）：用于 auto_excel 这类单条全局规则、无 ruleId 的提醒
     */
    public boolean existsForTypeAndDate(Integer type, Date runDate) {
        return repo.findFirstByTypeAndRelatedRunDate(type, runDate) != null;
    }

    /**
     * 按 type + runDate 删通知。auto_excel 执行成功后清当天的"提前提醒"，避免通知列表里
     * "3 天后将生成"和"已生成"并排展示给用户造成困惑。
     */
    @Transactional(rollbackFor = Exception.class)
    public void deleteByTypeAndRunDate(Integer type, Date runDate) {
        repo.deleteByTypeAndRelatedRunDate(type, runDate);
    }
}
