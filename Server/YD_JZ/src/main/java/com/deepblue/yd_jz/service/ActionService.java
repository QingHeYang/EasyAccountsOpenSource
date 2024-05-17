package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.action.Action;
import com.deepblue.yd_jz.dao.action.ActionDao;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ActionService {

    @Autowired
    ActionDao actionDao;

    @Transactional(rollbackFor = Exception.class)
    public void addAction(Action action) {
        actionDao.insertAction(action);
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateAction(int id, Action action) {
        action.setId(id);
        actionDao.updateAction(action);
    }

    @Transactional(rollbackFor = Exception.class)
    public List<Action> getActions() {
        return actionDao.getAction();
    }

    @Transactional(rollbackFor = Exception.class)
    public Action getAction(int id) {
        List<Action> actions = actionDao.getActionSingle(id);
        if (actions!=null&&actions.size()>0){
            return actions.get(0);
        }else {
            return null;
        }
    }
}
