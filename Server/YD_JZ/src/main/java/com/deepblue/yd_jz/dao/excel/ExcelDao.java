package com.deepblue.yd_jz.dao.excel;

import com.deepblue.yd_jz.dao.flow.Flow;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface ExcelDao {

    @Insert("insert into excel (e_date , e_name , e_path , condition , success) " +
            "values" +
            "(#{excel.eDate} , #{excel.eName} , #{excel.ePath} , #{excel.eCondition} , #{excel.success})")
    void addExcel(@Param("excel") Excel excel);
}
