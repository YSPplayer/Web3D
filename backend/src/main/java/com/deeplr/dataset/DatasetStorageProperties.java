package com.deeplr.dataset;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "deeplr.dataset")
public class DatasetStorageProperties {

  private Path rootDir;

  public Path getRootDir() {
    return rootDir;
  }

  public void setRootDir(Path rootDir) {
    this.rootDir = rootDir;
  }
}
