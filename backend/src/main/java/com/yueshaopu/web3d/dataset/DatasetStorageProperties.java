package com.yueshaopu.web3d.dataset;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "web3d.dataset")
public class DatasetStorageProperties {

  private Path rootDir;

  public Path getRootDir() {
    return rootDir;
  }

  public void setRootDir(Path rootDir) {
    this.rootDir = rootDir;
  }
}
