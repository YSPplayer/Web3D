package com.yueshaopu.web3d;

import com.yueshaopu.web3d.dataset.DatasetStorageProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(DatasetStorageProperties.class)
public class Web3dBackendApplication {

  public static void main(String[] args) {
    SpringApplication.run(Web3dBackendApplication.class, args);
  }
}
