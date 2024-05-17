package com.deepblue.yd_jz.controller.screen;

import com.deepblue.yd_jz.controller.flow.FlowBaseBean;
import com.deepblue.yd_jz.controller.home.ScreenFlowGetBean;
import com.deepblue.yd_jz.service.ScreenService;
import com.deepblue.yd_jz.utils.DataBean;
import com.deepblue.yd_jz.utils.LogUtils;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/screen")
public class ScreenController {
    @Autowired
    ScreenService screenService;

    @PostMapping("/getFlowByScreen")
    public DataBean<FlowBaseBean> getFlowByScreen(@RequestBody ScreenFlowGetBean screenFlowGetBean) {
        LogUtils.log_json(screenFlowGetBean);
       FlowBaseBean flowBaseBean =  screenService.getFlowByScreen(screenFlowGetBean);
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(flowBaseBean);
        return dataBean;
    }

    @PostMapping("/makeScreenExcel")
    public DataBean makeScreenExcel(@RequestBody ScreenFlowGetBean screenFlowGetBean) {
        return DataBean.setSuccessBean();
    }
    @PostMapping("/makeExcel")
    public DataBean makeScreenExcel(@RequestBody ScreenFlowGetBean screenFlowGetBean,@RequestParam String excelName) throws Exception {
        screenService.makeScreenExcel(screenFlowGetBean,excelName);
        DataBean dataBean = DataBean.setSuccessBean();
        dataBean.setData(excelName);
        return dataBean;
    }
}
