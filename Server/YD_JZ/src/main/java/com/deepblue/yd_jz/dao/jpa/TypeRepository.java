package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.Type;
import org.apache.ibatis.annotations.Param;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TypeRepository extends JpaRepository<Type, Integer> {
    // 查询指定parent并且t_disable为false和archive为false或null的记录
    @Query("SELECT t FROM Type t WHERE t.parent = :parent AND t.disable = false AND (t.archive IS NULL OR t.archive = false)")
    List<Type> findByParent(@Param("parent") int parent);

    @Query("SELECT t FROM Type t WHERE t.parent = :parent AND t.disable = false")
    List<Type> findByParentNoLimit(@Param("parent") int parent);

    // 查询t_disable为false和archive为false或null的记录
    @Query("SELECT t FROM Type t WHERE t.disable = false AND (t.archive IS NULL OR t.archive = false)")
    List<Type> findAllTypes();

    // 查询action_id为指定值或null的记录
    @Query("SELECT t FROM Type t WHERE (t.actionId = :actionId OR t.actionId IS NULL) AND t.disable = false AND (t.archive IS NULL OR t.archive = false)")
    List<Type> findByActionIdOrNull(@Param("actionId") Integer actionId);

    @Query("SELECT t FROM Type t WHERE t.archive = true")
    List<Type> findTypesByArchive();
}
