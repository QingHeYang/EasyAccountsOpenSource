# Token 认证并发问题修复开发日志

本文档记录 Token 滑动刷新的并发竞态条件问题及修复方案。

---

## 概览

| 项目 | 内容 |
|------|------|
| **分支** | 2.6.0 |
| **开发时间** | 2026-01-05 |
| **状态** | 已完成 |

---

## 问题描述

### 现象

并发请求时，部分请求返回 418 认证失败，日志如下：

```
17:24:26 exec-2: 请求 /action/getAction，token: 0534658e...
17:24:26 exec-3: 请求 /account/getAccount，同一个 token
17:24:26 exec-3: 认证失败 418 ❌
17:24:26 exec-2: Token 滑动刷新 ✅
17:24:26 exec-2: 认证成功 ✅
```

### 原因分析

`AuthUtils.isTokenValid()` 方法存在**竞态条件**：

1. 每次验证成功都会执行滑动刷新（写入文件）
2. 文件读写没有加锁保护
3. 并发时：
   - 线程 A 正在写入文件
   - 线程 B 同时读取文件 → 读到不完整数据
   - `Auth.decode()` 返回 null → 返回 418

### 问题代码

```java
private int isTokenValid(String token) {
    // 读取文件（无锁）
    String key = Okio.buffer(Okio.source(file)).readUtf8();
    Auth auth = Auth.decode(key);
    if (auth == null) {
        return 418;  // 读到不完整数据时触发
    }
    // ...
    // 每次都写入（无锁）
    saveAuth(auth);
}
```

---

## 解决方案

采用**双重保护**策略：

### 1. synchronized 锁保护

对整个读写操作加锁，确保同一时间只有一个线程操作文件：

```java
private static final Object FILE_LOCK = new Object();

private int isTokenValid(String token) {
    synchronized (FILE_LOCK) {
        // 读取、验证、写入都在锁内
    }
}
```

### 2. 减少刷新频率

只在剩余时间 < 50% 时才执行滑动刷新，大幅减少写操作：

```java
long totalDuration = expired * 60 * 1000;
long remainingTime = auth.getExpireTime() - currentTime;
if (remainingTime < totalDuration / 2) {
    // 才执行写入
    saveAuth(auth);
}
```

---

## 修复后代码

```java
@Slf4j
@Component
public class AuthUtils {

    private static final Object FILE_LOCK = new Object();

    @Value("${auth.expired}")
    private long expired;

    private int isTokenValid(String token) {
        File file = new File(authFolder + "/secret.key");
        synchronized (FILE_LOCK) {
            try {
                String key = Okio.buffer(Okio.source(file)).readUtf8();
                Auth auth = Auth.decode(key);
                if (auth == null) {
                    return 418;
                }
                long currentTime = System.currentTimeMillis();
                if (auth.getToken().equals(token) && auth.getExpireTime() > currentTime) {
                    // 滑动刷新：只在剩余时间 < 50% 时才刷新
                    long totalDuration = expired * 60 * 1000;
                    long remainingTime = auth.getExpireTime() - currentTime;
                    if (remainingTime < totalDuration / 2) {
                        long newExpireTime = currentTime + totalDuration;
                        auth.setExpireTime(newExpireTime);
                        saveAuth(auth);
                        log.info("Token 滑动刷新: 剩余{}分钟, 新过期时间 {}",
                                remainingTime / 60000, new java.util.Date(newExpireTime));
                    }
                    return 200;
                } else {
                    return 401;
                }
            } catch (IOException e) {
                log.error("Error reading key file: {}", e.getMessage());
                return 418;
            }
        }
    }
}
```

---

## 效果说明

### 并发请求处理流程

```
请求1: 获取锁 → 读文件 → 验证 → 写文件 → 释放锁
请求2: 等待锁... → 获取锁 → 读文件 → 验证 → (不写,剩余>50%) → 释放锁
请求3: 等待锁... → ...
```

### 性能影响

| 场景 | 影响 |
|------|------|
| 大部分请求 | 只读不写，锁持有时间极短（毫秒级） |
| 刷新请求 | 需要写文件，稍慢但仅在剩余 < 50% 时触发 |
| 排队等待 | 因操作很快，基本无感知 |

### 刷新策略示例

假设 `expired = 30` 分钟：

| 剩余时间 | 阈值 (50%) | 行为 |
|----------|------------|------|
| 25 分钟 | > 15 分钟 | 不刷新 |
| 15 分钟 | = 15 分钟 | 不刷新 |
| 10 分钟 | < 15 分钟 | 刷新 |
| 5 分钟 | < 15 分钟 | 刷新 |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `AuthUtils.java` | Token 认证工具类 |
| `TokenInterceptor.java` | 请求拦截器 |

---

## 418 状态码含义

在本项目中，418 表示**未注册**（无 secret.key 文件或文件损坏）：

| 返回码 | 含义 |
|--------|------|
| 200 | 认证成功 |
| 401 | Token 无效或过期 |
| 418 | 未注册（无密钥文件） |

---

*文档创建时间：2026-01-05*
