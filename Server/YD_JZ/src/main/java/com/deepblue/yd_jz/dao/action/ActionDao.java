package com.deepblue.yd_jz.dao.action;

import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ActionDao {


    @Insert("insert into action (h_name , exempt , handle) values (#{action.hName},#{action.exempt},#{action.handle})")
    void insertAction(@Param("action")Action action);

    @Update("update action set h_name=#{action.hName},exempt=#{action.exempt},handle=#{action.handle} where id = #{action.id}")
    void updateAction(@Param("action")Action action);

    @Select("select * from action")
    List<Action> getAction();

    @Select("select * from action where id = #{id}")
    List<Action> getActionSingle(@Param("id")int id);

}
