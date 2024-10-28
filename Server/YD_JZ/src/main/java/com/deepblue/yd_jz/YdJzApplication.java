package com.deepblue.yd_jz;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

import java.util.TimeZone;

@SpringBootApplication
@EnableJpaRepositories(basePackages = "com.deepblue.yd_jz.dao.jpa")
@MapperScan("com.deepblue.yd_jz.dao.mybatis")
public class YdJzApplication {
    private static final Logger logger = LogManager.getLogger(YdJzApplication.class);


    public static void main(String[] args) {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Shanghai"));
        SpringApplication.run(YdJzApplication.class, args);
        logger.debug("Application has started.");
    }

}
