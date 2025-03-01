package com.deepblue.yd_jz.dao.mybatis;

import com.deepblue.yd_jz.entity.Flow;
import com.deepblue.yd_jz.entity.FlowType;
import com.deepblue.yd_jz.entity.FlowYear;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

@Repository
public interface FlowDao {

        @Insert("insert into flow (" +
                        "f_date," +
                        "money," +
                        "type_id,action_id," +
                        "exempt,note," +
                        "f_create_date," +
                        "account_id," +
                        "account_to_id," +
                        "collect," +
                        "link_handle," +
                        "link_id," +
                        "automatic" +
                        ") values (" +
                        "#{flow.fDate}," +
                        "#{flow.money}," +
                        "#{flow.typeId},#{flow.actionId}," +
                        "#{flow.exempt},#{flow.note}," +
                        "#{flow.fCreateDate}," +
                        "#{flow.accountId}," +
                        "#{flow.accountToId}," +
                        "#{flow.collect}," +
                        "#{flow.linkHandle}," +
                        "#{flow.linkId}," +
                        "#{flow.automatic})")
        void addFlow(@Param("flow") Flow flow);

        @Select("select * from flow  where id = #{id} ")
        List<Flow> queryFlowById(@Param("id") int id);

        @Update("update flow set f_date= #{flow.fDate}, " +
                        "money = #{flow.money}," +
                        "link_handle = #{flow.linkHandle}," +
                        "link_id = #{flow.linkId}," +
                        "automatic = #{flow.automatic}," +
                        "type_id = #{flow.typeId}, action_id = #{flow.actionId}, " +
                        "exempt = #{flow.exempt} , note = #{flow.note}," +
                        "f_create_date=#{flow.fCreateDate}," +
                        "account_id=#{flow.accountId}," +
                        "account_to_id = #{flow.accountToId}," +
                        "collect =#{flow.collect}" +
                        " where id = #{flow.id} ")
        void updateFlow(@Param("flow") Flow flow);

        @Update("update flow set collect =#{collect} where id = #{id}")
        void collectFlowById(@Param("id") int id, @Param("collect") int collect);

        @SelectProvider(type = FlowSelectProvider.class, method = "getFlowByMain")
        List<Map<String, Object>> getFlowByMain(@Param("handle") int handle, int order, @Param("date") String date);

        @SelectProvider(type = FlowSelectProvider.class, method = "getFlowByScreen")
        List<Map<String, Object>> getFlowByScreen(int handle, int account, String startDate, String endDate,
                        boolean isSingleMonth, boolean isCollect, String note);

        @Delete("delete from flow where id = #{id}")
        void deleteFlowById(@Param("id") int id);

        @Delete("update flow set collect = #{collect} where id = #{id} ")
        void updateFlowCollect(@Param("id") int id, @Param("collect") int collect);

        @SelectProvider(type = FlowSelectProvider.class, method = "getYearlySummary")
        FlowYear getYearlySummary(@Param("year") int year);

        @Select("SELECT t.id, t.t_name, t.parent, SUM(CAST(f.money AS DECIMAL(10, 2))) AS money, tp.t_name as parentName "
                        +
                        "FROM flow f " +
                        "JOIN type t ON f.type_id = t.id " +
                        "LEFT JOIN type tp ON t.parent = tp.id " + // 联接parent type
                        "WHERE f.f_date LIKE #{datePattern} AND f.account_to_id = 0 " +
                        "GROUP BY t.id, t.t_name, t.parent, tp.t_name")
        List<FlowType> getFlowsByMonthAndType(@Param("datePattern") String datePattern);

        @SelectProvider(type = FlowSelectProvider.class, method = "getFlowsTypeByStartMonthAndEndMonth")
        List<FlowType> getFlowsTypeByStartMonthAndEndMonth(@Param("startMonth") String startMonth,
                        @Param("endMonth") String endMonth);

}
