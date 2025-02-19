package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.Action;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ActionRepository extends JpaRepository<Action, Integer> {
    // 你可以添加自定义查询方法，例如：
    List<Action> findByExempt(boolean exempt);
}