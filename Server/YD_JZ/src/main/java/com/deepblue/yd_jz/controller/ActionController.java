package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.service.ActionService;
import com.deepblue.yd_jz.dto.BaseDto;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/action")
@Slf4j
@Tag(name = "收支管理")
public class ActionController {
    @Autowired
    ActionService actionService;

    @Operation(summary = "添加收支")
    @PostMapping("/addAction")
    public BaseDto addAction(@RequestBody Action action) {
        actionService.addAction(action);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "更新收支")
    @PutMapping("/updateAction/{id}")
    public BaseDto updateAction(@PathVariable int id, @RequestBody Action action) {
        actionService.updateAction(id,action);
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "获取全部收支")
    @GetMapping("/getAction")
    public BaseDto<List<Action>> getActions(){
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(actionService.getActions());
        log.info(baseDto.toString());
        return baseDto;
    }

    @Operation(summary = "获取指定收支")
    @GetMapping("/getAction/{id}")
    public BaseDto<Action> getAction(@PathVariable int id){
        BaseDto baseDto = BaseDto.setSuccessBean();
        baseDto.setData(actionService.getAction(id));
        return baseDto;
    }
}
