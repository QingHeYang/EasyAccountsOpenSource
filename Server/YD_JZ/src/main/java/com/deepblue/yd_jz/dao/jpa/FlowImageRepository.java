package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.FlowImage;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface FlowImageRepository extends JpaRepository<FlowImage, Integer> {
    List<FlowImage> findByFlowId(Integer flowId);
    void deleteByFlowId(Integer flowId);
}