package com.deeplr.config;

import org.apache.ibatis.jdbc.ScriptRunner;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;
import javax.annotation.PostConstruct;
import javax.sql.DataSource;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
@Component
//初始化的时候检查数据库表是否存在，不存在则默认创建数据库表
public class DatabaseInitializer {
    @Autowired
    private DataSource dataSource;
    @Autowired
    private ResourceLoader resourceLoader;

    @Value("${deeplr.datasource.initialization-mode:always}")
    private String initializationMode;
    
    @PostConstruct
    public void InitDatabase() {
        if("always".equals(initializationMode)) {
            executeSqlFile("classpath:db/deeplr.sql");
        }
    }
    private void executeSqlFile(String sqlFilePath) {
        executeSql(sqlFilePath);
    }
    private void executeSql(String sqlFilePath) {
         try {
            Resource resource = resourceLoader.getResource(sqlFilePath);
            if (resource.exists()) {
                try (Connection connection = dataSource.getConnection()) {
                    ScriptRunner scriptRunner = new ScriptRunner(connection);
                    scriptRunner.setLogWriter(null);  // 关闭日志
                    scriptRunner.setErrorLogWriter(null);  // 关闭错误日志
                    
                    // 读取SQL文件
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
                        scriptRunner.runScript(reader);
                        System.out.println("SQL文件执行成功: " + sqlFilePath);
                    }
                }
            } else {
                System.err.println("SQL文件不存在: " + sqlFilePath);
            }
        } catch (Exception e) {
            System.err.println("执行SQL文件失败: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
