package com.deepblue.yd_jz.dao.account;

import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AccountDao {

    @Insert("insert into account(a_name,money,exempt_money,card,create_time,note) values (#{account.aName},#{account.money},#{account.exemptMoney},#{account.card},#{account.createTime},#{account.note})")
     void addAccount(@Param("account") Account account);

    @Update("update  account set a_name = #{aName},money = #{money},exempt_money = #{exemptMoney} ,card = #{card} ,note = #{note} where id = #{id}")
    void updateAccount(Account account);

    @Update("update  account set a_disable = true where id = #{id}")
    void disableAccount(@Param("id") String id);

    @Select("select id,money,exempt_money,a_name,card,create_time ,note from account where id = #{id} ")
    @ResultType(Account.class)
    List<Account> queryAccount(@Param("id") String id);

    @Select("select id,money,exempt_money,a_name,card,create_time,note from account where a_disable = 0")
    @ResultType(Account.class)
    List<Account> queryAllAccount();

    @Update("update account set money = #{money}, exempt_money = #{exemptMoney} where id = #{id}")
    void changeMoney(@Param("money")String money,@Param("exemptMoney")String exemptMoney,@Param("id") String id);

}
