package com.deeplr.dataset;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "deeplr.dataset")
public class DatasetStorageProperties {

  private String rootDir;

  public String getRootDir() {
    return rootDir;
  }

  public void setRootDir(String rootDir) {
    this.rootDir = rootDir;
  }

  public void setRootDir(Path rootDir) {
    this.rootDir = rootDir == null ? null : rootDir.toString();
  }
}
