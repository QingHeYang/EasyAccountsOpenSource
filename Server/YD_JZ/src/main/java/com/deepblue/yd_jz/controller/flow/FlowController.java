package com.deepblue.yd_jz.controller.flow;

import com.deepblue.yd_jz.service.ExcelService;
import com.deepblue.yd_jz.service.FlowService;
import com.deepblue.yd_jz.utils.DataBean;
import com.deepblue.yd_jz.utils.ExcelBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/flow")
public class FlowController {

    @Autowired
    FlowService flowService;

    @Autowired
    ExcelService excelService;

    @PostMapping("/addFlow")
    public DataBean addFlow(@RequestBody FlowGetBean flowGetBean) throws Exception {
        flowService.doAddFlow(flowGetBean);
        return DataBean.setSuccessBean();
    }


    @GetMapping("/getFlow/{id}")
    public DataBean<FlowToClientBean> getFlowById(@PathVariable int id) {
        FlowToClientBean flowToClientBean = flowService.doQueryFlow(id);
        DataBean<FlowToClientBean> dataBean = DataBean.setSuccessBean();
        if (flowToClientBean == null) {
            dataBean.setCode(403);
            dataBean.setMsg("未查询到该条记录");
        } else {
            dataBean.setData(flowToClientBean);
        }
        return dataBean;
    }

    @PutMapping("/updateFlow/{id}")
    public DataBean updateFlow(@PathVariable int id,@RequestBody FlowGetBean flowGetBean) throws Exception {
        flowService.doUpdateFlow(id,flowGetBean);
        return DataBean.setSuccessBean();
    }

    @PutMapping("/collectFlow/{id}/{collect}")
    public DataBean updateFlow(@PathVariable int id,@PathVariable int collect) throws Exception {
        flowService.doUpdateFlowCollect(id,collect);
        return DataBean.setSuccessBean();
    }

    @DeleteMapping("/deleteFlow/{id}")
    public DataBean deleteFlow(@PathVariable int id) throws Exception {
        flowService.doDeleteFlow(id);
        return DataBean.setSuccessBean();
    }

    @GetMapping("/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}")
    public DataBean<FlowBaseBean> getFlowListMain(@PathVariable int chooseHandle,@PathVariable int chooseOrder
            ,@PathVariable String date ){
        FlowBaseBean flowBaseBean = flowService.doGetMainBean(chooseHandle,chooseOrder,date);
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(flowBaseBean);
        return dataBean;
    }

    @GetMapping("/makeExcel/{date}")
    public DataBean<ExcelBean> getExcel(@PathVariable String date){
        ExcelBean excelBean =excelService.makeMonthExcel(date);
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(excelBean);
        return dataBean;
    }
}
