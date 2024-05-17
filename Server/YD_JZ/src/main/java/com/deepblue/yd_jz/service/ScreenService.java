package com.deepblue.yd_jz.service;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.ExcelWriter;
import com.alibaba.excel.write.metadata.WriteSheet;
import com.alibaba.excel.write.metadata.fill.FillWrapper;
import com.deepblue.yd_jz.controller.flow.FlowBaseBean;
import com.deepblue.yd_jz.controller.home.ScreenFlowGetBean;
import com.deepblue.yd_jz.dao.account.AccountDao;
import com.deepblue.yd_jz.dao.action.ActionDao;
import com.deepblue.yd_jz.dao.excel.Excel;
import com.deepblue.yd_jz.dao.excel.ExcelDao;
import com.deepblue.yd_jz.dao.excel.ScreenExcelBean;
import com.deepblue.yd_jz.dao.flow.FlowDao;
import com.deepblue.yd_jz.dao.type.TypeDao;
import com.deepblue.yd_jz.utils.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.*;

@Service
public class ScreenService {

    @Autowired
    ActionDao actionDao;

    @Autowired
    AccountDao accountDao;

    @Autowired
    FlowDao flowDao;

    @Autowired
    TypeDao typeDao;


    @Autowired
    ExcelDao excelDao;

    @Autowired
    FileMakeWebHook fileMakeWebHook;

    @Value("${excelScreenFolder}")
    public String excelFolder;

    @Value("${baseScreenExcel}")
    public String baseExcelPath;

    @Transactional(rollbackFor = Exception.class)
    public FlowBaseBean getFlowByScreen(ScreenFlowGetBean getBean) {
        List<Map<String, Object>> maps = flowDao.getFlowByScreen(getBean.getChooseHandle(),
                getBean.getAccountId(),
                getBean.getStartDate().trim(),
                getBean.getEndDate().trim(),
                getBean.isSingleMonth(),
                getBean.isCollect());
        FlowBaseBean baseBean = new FlowBaseBean();
        baseBean.setFlows(new ArrayList<>());
        BigDecimal moneyIn = new BigDecimal("0");
        BigDecimal moneyOut = new BigDecimal("0");
        BigDecimal totalEarn = new BigDecimal("0");
        HashMap<Integer, TMapBean> flowTypeMap = new HashMap();

        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        for (Map<String, Object> map : maps) {
            int typeId = (int) map.get("typeId");
            int parentTypeId = map.get("parentTypeId") == null ? -1 : (int) map.get("parentTypeId");

            int actionId = (int) map.get("actionId");
            boolean currentDataCanUse = false;
            if (!getBean.useTypeScreen() && !getBean.useActionScreen()) {//如果不筛选类型和操作
                currentDataCanUse = true;
            } else if (getBean.useTypeScreen() && !getBean.useActionScreen()) {//如果只筛选类型
                currentDataCanUse = getBean.getTypes().contains(typeId) || getBean.getTypes().contains(parentTypeId);
            } else if (!getBean.useTypeScreen() && getBean.useActionScreen()) {//如果只筛选操作
                currentDataCanUse = getBean.getActions().contains(actionId);
            } else if (getBean.useTypeScreen() && getBean.useActionScreen()) {//如果同时筛选类型和操作
                currentDataCanUse = (getBean.getTypes().contains(typeId) || getBean.getTypes().contains(parentTypeId)) && getBean.getActions().contains(actionId);
            }
            if (currentDataCanUse) {
                FlowBaseBean.FlowInnerBean innerBean = new FlowBaseBean.FlowInnerBean();
                innerBean.setId((Integer) map.get("id"));
                innerBean.setMoney((String) map.get("money"));
                innerBean.setExempt((Boolean) map.get("exempt"));
                innerBean.setCollect((Boolean) map.get("collect"));
                innerBean.setHandle((Integer) map.get("handle"));
                innerBean.sethName((String) map.get("handleName"));
                innerBean.setNote((String) map.get("note"));
                Date fDate = (Date) map.get("flowDate");
                innerBean.setfDate(sdf.format(fDate));
                innerBean.setaName((String) map.get("accountName"));
                innerBean.setToAName((String) map.get("toAccountName"));
                if (map.get("parentTypeName") != null) {
                    innerBean.settName(map.get("parentTypeName") + "/" + map.get("typeName"));
                } else {
                    innerBean.settName((String) map.get("typeName"));
                }
                baseBean.getFlows().add(innerBean);
                if (innerBean.getHandle() == 1) {
                    moneyOut = moneyOut.add(new BigDecimal(innerBean.getMoney()));
                } else if (innerBean.getHandle() == 0) {
                    moneyIn = moneyIn.add(new BigDecimal(innerBean.getMoney()));
                }

                if (flowTypeMap.get(typeId) == null) {//如果当前type对象为空
                    TMapBean tMapBean = new TMapBean();
                    tMapBean.setTypeId(typeId);
                    tMapBean.setTypeName((String) map.get("typeName"));
                    BigDecimal bigDecimal = new BigDecimal(innerBean.getMoney());
                    tMapBean.setMoneyDeci(bigDecimal);
                    tMapBean.setParent(parentTypeId == -1);
                    tMapBean.setParentId(parentTypeId);
                    flowTypeMap.put(typeId, tMapBean);
                    if (parentTypeId != -1 && flowTypeMap.get(parentTypeId) == null) {//如果当前对象不是一级分类  &&  父类对象为空
                        TMapBean parentBean = new TMapBean();
                        parentBean.setTypeId(parentTypeId);
                        parentBean.setTypeName((String) map.get("parentTypeName"));
                        BigDecimal parentDecimal = new BigDecimal(innerBean.getMoney());
                        parentBean.setMoneyDeci(parentDecimal);
                        parentBean.setParent(true);
                        flowTypeMap.put(parentTypeId, parentBean);
                    } else if (parentTypeId != -1 && flowTypeMap.get(parentTypeId) != null) {//如果当前对象不是一级分类  &&  父类对象不为空
                        BigDecimal result = flowTypeMap.get(parentTypeId).getMoneyDeci().add(new BigDecimal(innerBean.getMoney()));
                        flowTypeMap.get(parentTypeId).setMoneyDeci(result);
                    }
                } else {//如果不为空的话 则取出并加上当前金额
                    BigDecimal resultChild = flowTypeMap.get(typeId).getMoneyDeci().add(new BigDecimal(innerBean.getMoney()));
                    flowTypeMap.get(typeId).setMoneyDeci(resultChild);
                    if (parentTypeId != -1) { //如果当前不是子分类的话 夫分类得加金额
                        BigDecimal resultParent= flowTypeMap.get(parentTypeId).getMoneyDeci().add(new BigDecimal(innerBean.getMoney()));
                        flowTypeMap.get(parentTypeId).setMoneyDeci(resultParent);
                    }
                }
            }
        }
        baseBean.setTypeList(exChangeMapToList(flowTypeMap));
        totalEarn = moneyIn.subtract(moneyOut);
        baseBean.setTotalIn(moneyIn.toString());
        baseBean.setTotalOut(moneyOut.toString());
        baseBean.setTotalEarn(totalEarn.toString());
        return baseBean;
    }

    private List<FlowBaseBean.TypeBean> exChangeMapToList(HashMap<Integer, TMapBean> typeMap) {
        List<FlowBaseBean.TypeBean> typeBeanList = new ArrayList<>();
        typeMap.forEach((integer, tMapBean) -> {
            if (tMapBean.isParent()) {
                FlowBaseBean.TypeBean tl = exchangePoJo(tMapBean);
                tl.setChildren(new ArrayList<>());
                typeBeanList.add(tl);
            }
        });

        typeMap.forEach(((integer, tMapBean) -> {
            if (!tMapBean.isParent()) {
                typeBeanList.forEach(item -> {
                    if (tMapBean.getParentId() == item.getTypeId()) {
                        FlowBaseBean.TypeBean child =exchangePoJo(tMapBean);
                        item.getChildren().add(child);
                    }
                });
            }
        }));
        return typeBeanList;
    }

    private FlowBaseBean.TypeBean exchangePoJo(TMapBean tMapBean) {
        FlowBaseBean.TypeBean tl = new FlowBaseBean.TypeBean();
        tl.setParent(tMapBean.isParent());
        tl.setTypeName(tMapBean.getTypeName());
        tl.setMoney(tMapBean.getMoneyDeci().toString());
        tl.setTypeId(tMapBean.getTypeId());
        return tl;
    }

    @Transactional(rollbackFor = Exception.class)
    public void makeScreenExcel(ScreenFlowGetBean screenFlowGetBean, String excelName) throws Exception {
        FlowBaseBean flowBaseBean = getFlowByScreen(screenFlowGetBean);
        if (flowBaseBean.getFlows().size() == 0) {
            throw new Exception("所选size 为0");
        }
        ScreenExcelBean excelBean = new ScreenExcelBean();
        excelBean.setFlow(new ArrayList<>());
        flowBaseBean.getFlows().forEach((item) -> {
            ExcelBean.Flow flow = new ExcelBean.Flow();
            flow.setFlowDate(item.getfDate());
            flow.setAccountName(item.getaName());
            flow.setTypeName(item.gettName());
            flow.setNote(item.getNote());
            flow.setActionName(item.gethName());
            flow.setMoney(item.getMoney());
            excelBean.getFlow().add(flow);
        });
        excelBean.setTotalIn(flowBaseBean.getTotalIn());
        excelBean.setTotalOut(flowBaseBean.getTotalOut());
        excelBean.setDate(screenFlowGetBean.getStartDate() + " 至 " + screenFlowGetBean.getEndDate());
        excelBean.setName(excelName);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmmss");
        String dateStr = sdf.format(new Date());
        excelName = excelName + "_" + dateStr + ".xls";
        String excelPath = doMakeExcel(excelBean, excelName);
        uploadExcel(excelPath, excelName + ".xls", excelBean.getName());
    }

    private void uploadExcel(String excelPath, String excelFileName, String title) {
        if (FileUtils.isExist(excelPath)) {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
            String dateStr = sdf.format(new Date());
            fileMakeWebHook.sendFile(new File(excelPath), "screen_excel", excelFileName);
            /*ossUtils.doUpload(new File(excelPath), "YD_JZ/excel/screen/", excelFileName, new OssUtils.OssUploadCallBack() {
                @Override
                public void onUploadSuccess(String ossUrl) {
                    LogUtils.log_print("上传完成，地址为： " + ossUrl);
                    Excel excel = new Excel();
                    excel.setSuccess(1);
                    excel.seteDate(dateStr);
                    excel.setePath(ossUrl);
                    excel.seteCondition("sdf");
                    excel.seteName(title);
                    excelDao.addExcel(excel);
                    emailUtils.setTitle("筛选结果报表：  " + title);
                    emailUtils.setContent("报表已生成");
                    emailUtils.sendEmail(ossUrl);
                }

                @Override
                public void onUploadFailed(String msg) {
                    LogUtils.log_print("上传失败: " + msg);
                    Excel excel = new Excel();
                    excel.setSuccess(0);
                    excel.seteDate(dateStr);
                    excel.setePath("");
                    excel.seteCondition("sdf");
                    excel.seteName(title);
                    excelDao.addExcel(excel);

                }
            });*/
        }
    }

    private void sendEmail(String fileUrl, String title) {
       /* emailUtils.setTitle(title);
        emailUtils.sendEmail(fileUrl);*/
    }

    private String doMakeExcel(ScreenExcelBean excelBean, String excelName) {
        String excelPath = excelFolder + excelName;
        ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
                .withTemplate(baseExcelPath)
                .registerWriteHandler(new ExcelService.ExcelWriteHandler())
                .build();
        WriteSheet writeSheet = EasyExcel.writerSheet().build();
        excelWriter.fill(excelBean, writeSheet);
        excelWriter.fill(new FillWrapper("flow", excelBean.getFlow()), writeSheet);
        excelWriter.finish();
        return excelPath;
    }


    public static class TMapBean {
        private String typeName;
        private int typeId;

        private int parentId;
        private boolean parent;
        private BigDecimal moneyDeci;

        public int getParentId() {
            return parentId;
        }

        public void setParentId(int parentId) {
            this.parentId = parentId;
        }

        public boolean isParent() {
            return parent;
        }

        public void setParent(boolean parent) {
            this.parent = parent;
        }

        public BigDecimal getMoneyDeci() {
            return moneyDeci;
        }

        public void setMoneyDeci(BigDecimal moneyDeci) {
            this.moneyDeci = moneyDeci;
        }

        public String getTypeName() {
            return typeName;
        }

        public void setTypeName(String typeName) {
            this.typeName = typeName;
        }


        public int getTypeId() {
            return typeId;
        }

        public void setTypeId(int typeId) {
            this.typeId = typeId;
        }
    }

}
