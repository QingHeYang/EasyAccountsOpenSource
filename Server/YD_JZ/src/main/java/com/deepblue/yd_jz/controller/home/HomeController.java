package com.deepblue.yd_jz.controller.home;

import com.deepblue.yd_jz.controller.flow.FlowBaseBean;
import com.deepblue.yd_jz.service.HomeService;
import com.deepblue.yd_jz.service.ScreenService;
import com.deepblue.yd_jz.utils.DataBean;

import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/home")
public class HomeController {
    @Autowired
    HomeService homeService;

    @Autowired
    ScreenService screenService;

    @Value("${webhook_url}")
    private String webhookUrl;

    @GetMapping("/getHomeInfo")
    public DataBean<HomeBean> getHomeInfo() {
        log.info("\n\n\n"+webhookUrl+"\n\n\n");
        HomeBean homeBean = homeService.getHomeBean();
        DataBean dataBean = new DataBean();
        dataBean.setData(homeBean);
        return dataBean;
    }
}
