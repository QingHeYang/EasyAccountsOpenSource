# Log4j2 滚动日志配置开发日志

本文档记录 Log4j2 日志滚动策略的配置优化。

---

## 概览

| 项目 | 内容 |
|------|------|
| **分支** | 2.6.0 |
| **开发时间** | 2026-01-05 |
| **状态** | 已完成 |

---

## 问题描述

**现象：** 滚动日志文件 `app-rolling-*.log` 从 9 月份一直保留到当前（1 月），没有自动删除旧文件。

**原因分析：**

`DefaultRolloverStrategy` 的 `max` 属性只控制**同一时间段内**（如同一天）因大小触发滚动产生的文件数量上限（即 `filePattern` 中 `%i` 的最大值），**不会自动删除按时间滚动的旧文件**。

```xml
<!-- max="20" 只限制同一天内的 %i 索引，不会删除旧日期的文件 -->
<DefaultRolloverStrategy max="20"/>
```

---

## 解决方案

添加 `Delete` 操作，配合 `IfFileName` 和 `IfLastModified` 条件自动删除旧日志。

### 修改前

```xml
<RollingFile name="RollingFileLogger"
             fileName="${log-path}/app-rolling.log"
             filePattern="${log-path}/app-rolling-%d{yyyy-MM-dd}-%i.log">
    <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss} [%t] %-5level %logger{36} - %msg%n"/>
    <Policies>
        <TimeBasedTriggeringPolicy/>
        <SizeBasedTriggeringPolicy size="10MB"/>
    </Policies>
    <DefaultRolloverStrategy max="20"/>
</RollingFile>
```

### 修改后

```xml
<RollingFile name="RollingFileLogger"
             fileName="${log-path}/app-rolling.log"
             filePattern="${log-path}/app-rolling-%d{yyyy-MM-dd}-%i.log">
    <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss} [%t] %-5level %logger{36} - %msg%n"/>
    <Policies>
        <OnStartupTriggeringPolicy/>
        <TimeBasedTriggeringPolicy/>
        <SizeBasedTriggeringPolicy size="10MB"/>
    </Policies>
    <DefaultRolloverStrategy max="20">
        <Delete basePath="${log-path}" maxDepth="1">
            <IfFileName glob="app-rolling-*.log"/>
            <IfLastModified age="P10D"/>
        </Delete>
    </DefaultRolloverStrategy>
</RollingFile>
```

---

## 配置说明

### 触发策略 (Policies)

| 策略 | 说明 |
|------|------|
| `OnStartupTriggeringPolicy` | 应用启动时触发滚动（同时触发删除旧文件） |
| `TimeBasedTriggeringPolicy` | 按时间滚动（根据 filePattern 中的日期格式，此处为每天） |
| `SizeBasedTriggeringPolicy` | 按大小滚动（超过 10MB 滚动） |

### 删除策略 (Delete)

| 属性/条件 | 值 | 说明 |
|-----------|-----|------|
| `basePath` | `${log-path}` | 日志目录 |
| `maxDepth` | `1` | 只扫描当前目录，不递归子目录 |
| `IfFileName glob` | `app-rolling-*.log` | 匹配的文件名模式 |
| `IfLastModified age` | `P10D` | 删除 10 天前的文件 |

### age 格式

使用 ISO 8601 Duration 格式：

| 格式 | 含义 |
|------|------|
| `P10D` | 10 天 |
| `P30D` | 30 天 |
| `P90D` | 90 天 |
| `PT12H` | 12 小时 |

---

## 注意事项

1. **删除时机**：Delete 操作只在滚动时触发。添加 `OnStartupTriggeringPolicy` 可确保启动时也会清理旧日志。

2. **glob 匹配**：确保 `IfFileName glob` 的模式与 `filePattern` 生成的文件名一致。

3. **maxDepth 参数**：
   - `maxDepth="1"` - 只删除 basePath 目录下的文件
   - `maxDepth="2"` - 包含一层子目录

4. **组合条件**：可以组合多个条件，如同时限制天数和总大小：
   ```xml
   <Delete basePath="${log-path}" maxDepth="1">
       <IfFileName glob="app-rolling-*.log"/>
       <IfAny>
           <IfLastModified age="P10D"/>
           <IfAccumulatedFileSize exceeds="500MB"/>
       </IfAny>
   </Delete>
   ```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `YD_JZ/src/main/resources/log4j2.xml` | Log4j2 配置文件 |

---

## 参考资料

- [Apache Log4j Rolling File Appenders](https://logging.apache.org/log4j/2.x/manual/appenders/rolling-file.html)
- [Log4j2 - Delete Old Logs on Rollover](https://howtodoinjava.com/java/delete-logs-on-rollover/)
- [A Guide to Rolling File Appenders - Baeldung](https://www.baeldung.com/java-logging-rolling-file-appenders)

---

*文档创建时间：2026-01-05*
