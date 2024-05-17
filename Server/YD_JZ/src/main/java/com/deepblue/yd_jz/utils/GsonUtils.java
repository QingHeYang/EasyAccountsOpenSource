package com.deepblue.yd_jz.utils;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.LongSerializationPolicy;

public class GsonUtils {

    public static Gson gson = new GsonBuilder()
            .serializeNulls()
            .setLongSerializationPolicy(LongSerializationPolicy.STRING)
            .disableHtmlEscaping()
            .create();
}
