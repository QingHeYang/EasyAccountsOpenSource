package com.deepblue.yd_jz.utils;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import lombok.extern.slf4j.Slf4j;
import org.apache.http.util.TextUtils;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.stereotype.Component;

import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

@Component
@Slf4j
public class LogUtils {

    public static void log_print(String msg) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String time = sdf.format(new Date());
        String top = "\n\n----------------------"+time+"-----------------------";
        msg = "\n\n" + msg;
        String end = "\n----------------------------------------------------------------";
        log.info(top+setStackTrace() + msg + end);
    }

    public static void log_json(Object obj) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String time = sdf.format(new Date());
        String top = "\n\n----------------------"+time+"-----------------------";

        String msg = "";
        Gson gson = new Gson();
        JsonElement element = gson.toJsonTree(obj);
        if (element.isJsonArray()) {
            JSONArray jsonArray = new JSONArray(obj);
            msg ="\n\n"+ jsonArray.toString(4);
        } else {
            JSONObject jsonObject = new JSONObject(obj);
            msg ="\n\n"+ jsonObject.toString(4);
        }
        String end = "\n----------------------------------------------------------------";
        log.info(top+setStackTrace() + msg + end);
    }

    private static String setStackTrace() {
        List<StackTraceElement> steList = Arrays.asList(Thread.currentThread().getStackTrace());
        StackTraceElement ste = steList.get(3);
        if (ste == null) {
            return "";
        }
        String fileName = ste.getFileName();
        if (TextUtils.isEmpty(fileName)) {
            return "";
        }
        return "\n"+fileName+"  at " + ste.toString() ;
    }
}
