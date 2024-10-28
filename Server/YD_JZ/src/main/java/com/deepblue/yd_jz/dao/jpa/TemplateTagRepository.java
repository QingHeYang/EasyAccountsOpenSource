package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.TemplateTag;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;


@Repository
public interface TemplateTagRepository extends JpaRepository<TemplateTag, Integer> {
    // 可以在这里添加查找特定标签的自定义方法，例如根据名字查询
}
