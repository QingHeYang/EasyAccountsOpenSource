package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.dao.jpa.ActionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ActionService {

    @Autowired
    private ActionRepository actionRepository; // Updated to use JPA repository

    @Autowired
    private FlowTemplateService flowTemplateService;


    @Transactional(rollbackFor = Exception.class)
    public void addAction(Action action) {
        actionRepository.save(action); // JPA repository method for creating or updating
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateAction(int id, Action action) {
        action.setId(id);
        actionRepository.save(action); // JPA repository method for creating or updating
    }

    // v2.6.0: 只返回未禁用的收支类型
    @Transactional(rollbackFor = Exception.class)
    public List<Action> getActions() {
        return actionRepository.findByDisableFalse();
    }

    // v2.6.0: 返回全部收支类型（包括禁用的，管理页面用）
    @Transactional(rollbackFor = Exception.class)
    public List<Action> getAllActions() {
        return actionRepository.findAll();
    }

    @Transactional(rollbackFor = Exception.class)
    public Action getAction(int id) {
        return actionRepository.findById(id).orElse(null); // JPA repository method for finding by id
    }

    // v2.6.0: 禁用收支类型，同时清除引用该收支的快记模板
    @Transactional(rollbackFor = Exception.class)
    public void disableAction(int id) {
        actionRepository.findById(id).ifPresent(action -> {
            action.setDisable(true);
            actionRepository.save(action);
            flowTemplateService.clearAction(id);
        });
    }

}
