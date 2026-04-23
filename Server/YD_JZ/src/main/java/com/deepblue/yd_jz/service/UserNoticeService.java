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
}
