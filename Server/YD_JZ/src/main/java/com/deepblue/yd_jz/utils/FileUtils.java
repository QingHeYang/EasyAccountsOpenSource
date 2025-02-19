package com.deepblue.yd_jz.utils;

import jdk.jfr.StackTrace;
import okio.Okio;
import org.springframework.stereotype.Component;

import java.io.File;
@Component
public class FileUtils {

    public static boolean isExist(String path){
        File file = new File(path);
        boolean isExist = file.exists();
        LogUtils.log_print("送检文件："+path+"  是否存在："+isExist);
        return isExist;
    }


}
