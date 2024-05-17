package com.deepblue.yd_jz.controller.action;

import com.deepblue.yd_jz.dao.action.Action;
import com.deepblue.yd_jz.dao.type.Type;
import com.deepblue.yd_jz.service.ActionService;
import com.deepblue.yd_jz.utils.DataBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/action")
public class ActionController {
    @Autowired
    ActionService actionService;

    @PostMapping("/addAction")
    public DataBean addAction(@RequestBody Action action) {
        actionService.addAction(action);
        return DataBean.setSuccessBean();
    }

    @PutMapping("/updateAction/{id}")
    public DataBean updateAction(@PathVariable int id,@RequestBody Action action) {
        actionService.updateAction(id,action);
        return DataBean.setSuccessBean();
    }

    @GetMapping("/getAction")
    public DataBean<List<Action>> getActions(){
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(actionService.getActions());
        return dataBean;
    }

    @GetMapping("/getAction/{id}")
    public DataBean<Action> getAction(@PathVariable int id){
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(actionService.getAction(id));
        return dataBean;
    }
}
