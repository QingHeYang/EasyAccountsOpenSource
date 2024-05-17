package com.deepblue.yd_jz.dao.type;

import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TypeDao {

    @Insert("insert into type (t_name , parent) values (#{type.tName},#{type.parent})")
    void addType(@Param("type") Type type);

    @Update("update type set t_name = #{type.tName},parent = #{type.parent} where id = #{type.id}")
    void updateType(@Param("type") Type type);

    @Update("update type set t_disable = true where id = #{id}")
    void disableType(@Param("id" )int id);

    @Select("select * from type where parent = #{parent} and t_disable = 0")
    List<Type> queryTypeList(@Param("parent") int parent);

    @Select("select * from type where id = #{id}  and t_disable = 0")
    List<Type> queryTypeSingle(@Param("id") int id);

    @Select("select * from type where  t_disable = 0")
    List<Type> queryAllType();

    @Update("update type set parent = '-1' where parent = #{parent}")
    void setDisableTypeChild(@Param("parent") int parent);

}
