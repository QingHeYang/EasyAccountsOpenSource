package com.deepblue.yd_jz.dao.jpa;
import com.deepblue.yd_jz.entity.Account;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AccountRepository extends JpaRepository<Account, Integer> {
    List<Account> findByDisableFalse();
}
