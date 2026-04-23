package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.AppConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AppConfigRepository extends JpaRepository<AppConfig, Integer> {

    // 按 (domain, key) 取单条配置
    AppConfig findByDomainAndConfigKey(String domain, String configKey);

    // 按 domain 取一组配置（整个业务域的全部 k-v）
    List<AppConfig> findByDomain(String domain);
}
