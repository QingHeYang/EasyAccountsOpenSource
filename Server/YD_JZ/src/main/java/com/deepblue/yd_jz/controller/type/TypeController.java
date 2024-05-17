package com.deepblue.yd_jz.controller.type;

import com.deepblue.yd_jz.controller.account.AccountPostBean;
import com.deepblue.yd_jz.dao.type.Type;
import com.deepblue.yd_jz.service.AccountService;
import com.deepblue.yd_jz.service.TypeService;
import com.deepblue.yd_jz.utils.DataBean;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Update;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/type")
public class TypeController {
    @Autowired
    TypeService typeService;

    @PostMapping("/addType")
    public DataBean addType(@RequestBody Type type) {
        if (type.getParent()==null){
            type.setParent(-1);
        }
        typeService.addType(type);
        return DataBean.setSuccessBean();
    }

    @PutMapping("/updateType/{id}")
    public DataBean updateType(@PathVariable int id,@RequestBody Type type){
        type.setId(id);
        if (type.getParent()==null){
            type.setParent(-1);
        }
        typeService.updateType(type);
        return DataBean.setSuccessBean();
    }

    @DeleteMapping("/deleteType/{id}")
    public DataBean deleteType(@PathVariable int id){
        typeService.disableType(id);
        return DataBean.setSuccessBean();
    }

    @GetMapping("/getType/{parent}")
    public DataBean<List<Type>> getType(@PathVariable int parent){
        DataBean<List<Type>> dataBean = DataBean.setSuccessBean();
        dataBean.setData(typeService.queryTypeList(parent));
        return dataBean;
    }

    @GetMapping("/getType")
    public DataBean<List<TypeToClient>> getType(){
        List<TypeToClient> toClients = typeService.queryAllType();
        DataBean<List<TypeToClient>> dataBean = DataBean.setSuccessBean();
        dataBean.setData(toClients);
        return dataBean;
    }

    @GetMapping("/getTypeSingle/{id}")
    public DataBean<Type> getTypeSingle(@PathVariable int id){
        DataBean<Type> dataBean = DataBean.setSuccessBean();
        dataBean.setData(typeService.queryTypeSingle(id));
        return dataBean;
    }

}
