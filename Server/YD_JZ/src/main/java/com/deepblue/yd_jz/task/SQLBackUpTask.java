package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.utils.FileMakeWebHook;
import com.deepblue.yd_jz.utils.FileUtils;
import com.deepblue.yd_jz.utils.LogUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

@Slf4j
@Configuration      //1.主要用于标记配置类，兼备Component的效果。
@EnableScheduling
public class SQLBackUpTask {

    @Value("${sqlBackUpFolder}")
    String sqlBackupFolder;
    Action action;

    @Value("${sqldumpCmd}")
    String sqldumpCmd;

    @Value("${webhook_url}")
    String webhookUrl;

    @Autowired
    FileMakeWebHook fileMakeWebHook;

    @Scheduled(cron = "${cron.sqlBackupTime}")
    public void doOutSqlFile() {

        String fileName = "yd_jz_";
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmm");
        String time = sdf.format(new Date());

        fileName = fileName + time + ".sql";
        LogUtils.log_print("开始备份sql\n" + "未生成文件地址--------------- " + sqlBackupFolder + fileName);
        String[] cmd = new String[]{"/bin/sh", "-c", sqldumpCmd + sqlBackupFolder + fileName};
        try {
           Process p =  Runtime.getRuntime().exec(cmd);
           p.waitFor();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

        if (FileUtils.isExist(sqlBackupFolder + fileName)) {
            log.info(webhookUrl+fileName);
            fileMakeWebHook.sendFile(new File(sqlBackupFolder + fileName), "sql", fileName);
        }

    }
}
