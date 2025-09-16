package com.deepblue.yd_jz.utils;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * 金额处理工具类
 * 用于统一处理金额的格式化，避免精度问题
 */
public class MoneyUtils {
    
    /**
     * 格式化金额字符串，保留2位小数
     * @param money 原始金额字符串
     * @return 格式化后的金额字符串
     */
    public static String formatMoney(String money) {
        if (money == null || money.trim().isEmpty()) {
            return "0.00";
        }
        
        try {
            BigDecimal decimal = new BigDecimal(money.trim());
            // 保留2位小数，四舍五入
            return decimal.setScale(2, RoundingMode.HALF_UP).toString();
        } catch (NumberFormatException e) {
            LogUtils.log_print("金额格式化失败: " + money);
            return "0.00";
        }
    }
    
    /**
     * 金额相加并格式化
     * @param money1 金额1
     * @param money2 金额2
     * @return 格式化后的总金额
     */
    public static String addMoney(String money1, String money2) {
        BigDecimal decimal1 = new BigDecimal(formatMoney(money1));
        BigDecimal decimal2 = new BigDecimal(formatMoney(money2));
        return decimal1.add(decimal2).setScale(2, RoundingMode.HALF_UP).toString();
    }
    
    /**
     * 金额相减并格式化
     * @param money1 被减数
     * @param money2 减数
     * @return 格式化后的差额
     */
    public static String subtractMoney(String money1, String money2) {
        BigDecimal decimal1 = new BigDecimal(formatMoney(money1));
        BigDecimal decimal2 = new BigDecimal(formatMoney(money2));
        return decimal1.subtract(decimal2).setScale(2, RoundingMode.HALF_UP).toString();
    }
    
    /**
     * 验证金额格式是否正确
     * @param money 金额字符串
     * @return 是否为有效金额
     */
    public static boolean isValidMoney(String money) {
        if (money == null || money.trim().isEmpty()) {
            return false;
        }
        
        try {
            BigDecimal decimal = new BigDecimal(money.trim());
            // 检查是否为负数
            if (decimal.compareTo(BigDecimal.ZERO) < 0) {
                return false;
            }
            // 检查小数位数是否超过2位
            String[] parts = money.split("\\.");
            if (parts.length > 1 && parts[1].length() > 2) {
                return false;
            }
            return true;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}