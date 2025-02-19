package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.FlowTemplate;
import com.deepblue.yd_jz.entity.TemplateTag;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FlowTemplateRepository  extends JpaRepository<FlowTemplate, Integer> {

    List<FlowTemplate> findFlowTemplateByTagId(Integer tagId);

    @Query("SELECT f FROM FlowTemplate f WHERE f.actionId = :actionId")
    List<FlowTemplate> findFlowTemplatesByActionId(Integer actionId);

    @Query("SELECT f FROM FlowTemplate f WHERE f.typeId = :typeId")
    List<FlowTemplate> findFlowTemplatesByTypeId(Integer typeId);

    @Query("SELECT f FROM FlowTemplate f WHERE f.accountId = :accountId")
    List<FlowTemplate> findFlowTemplatesByAccountId(Integer accountId);
}
