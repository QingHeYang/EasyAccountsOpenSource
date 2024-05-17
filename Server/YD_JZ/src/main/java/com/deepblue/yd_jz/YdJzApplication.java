package com.deepblue.yd_jz;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

import java.util.TimeZone;

@SpringBootApplication
@MapperScan(value = "com.deepblue.yd_jz")
public class YdJzApplication {
    private static final Logger logger = LogManager.getLogger(YdJzApplication.class);


    public static void main(String[] args) {
        TimeZone.setDefault(TimeZone.getTimeZone("GMT+8"));
        SpringApplication.run(YdJzApplication.class, args);
        logger.debug("Application has started.");
    }

}
