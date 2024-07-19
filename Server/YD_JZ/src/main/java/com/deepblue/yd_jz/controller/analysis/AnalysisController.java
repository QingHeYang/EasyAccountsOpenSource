package com.deepblue.yd_jz.controller.analysis;

import com.deepblue.yd_jz.service.AnalysisService;
import com.deepblue.yd_jz.utils.DataBean;
import com.deepblue.yd_jz.utils.ExcelBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/analysis")
public class AnalysisController {
    @Autowired
    AnalysisService analysisService;

    @GetMapping("/doAnalysis")
    public DataBean<AnalysisBean> doAnalysis(@RequestParam("start") String start, @RequestParam(value = "end", required = false) String end) {
        DataBean dataBean = DataBean.setSuccessBean();
        AnalysisBean analysisBean =analysisService.doAnalysis(start, end);
        dataBean.setData(analysisBean);
        return dataBean;
    }

    @GetMapping("/exportExcel")
    public DataBean<ExcelBean> exportExcel(@RequestParam("start") String start, @RequestParam(value = "end", required = false) String end) {
        DataBean dataBean = DataBean.setSuccessBean();
        AnalysisExcelBean excelBean = analysisService.doMakeAnalysisExcel(start, end);
        dataBean.setData(excelBean);
        return dataBean;
    }
}
