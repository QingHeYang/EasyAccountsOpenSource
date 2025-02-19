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


    @Transactional(rollbackFor = Exception.class)
    public void addAction(Action action) {
        actionRepository.save(action); // JPA repository method for creating or updating
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateAction(int id, Action action) {
        action.setId(id);
        actionRepository.save(action); // JPA repository method for creating or updating
    }

    @Transactional(rollbackFor = Exception.class)
    public List<Action> getActions() {
        return actionRepository.findAll(); // JPA repository method for retrieving all records
    }

    @Transactional(rollbackFor = Exception.class)
    public Action getAction(int id) {
        return actionRepository.findById(id).orElse(null); // JPA repository method for finding by id
    }

}
