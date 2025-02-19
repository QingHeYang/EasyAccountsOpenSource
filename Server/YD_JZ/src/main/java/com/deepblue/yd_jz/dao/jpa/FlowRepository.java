package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.Flow;
import com.deepblue.yd_jz.entity.FlowJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface FlowRepository  extends JpaRepository<FlowJpaEntity,Integer> {
    // 根据年份查询该年份的所有Flow
    @Query("SELECT f FROM FlowJpaEntity f WHERE f.fDate LIKE CONCAT(:year, '%')")
    List<FlowJpaEntity> findByYear(@Param("year") Integer year);


    @Query("SELECT f FROM FlowJpaEntity f JOIN f.action a " +
            "WHERE a.handle IN (0, 1) " +
            "  AND f.fDate BETWEEN :startDate AND :endDate")
    List<FlowJpaEntity> findFlowsByHandleAndDateRange(
            @Param("startDate") String startDate,
            @Param("endDate")   String endDate);

    @Query("SELECT f FROM FlowJpaEntity f JOIN f.action a " +
            "WHERE a.handle IN (0, 1) " +
            "  AND f.fDate BETWEEN :startDate AND :endDate " +
            "  AND f.type.id = :typeId")
    List<FlowJpaEntity> findByFDateBetweenAndType(String startDate, String endDate, Integer typeId);

    @Query("SELECT f FROM FlowJpaEntity f WHERE f.fDate > :date")
    List<FlowJpaEntity> findByFDateAfter(String date);
}
