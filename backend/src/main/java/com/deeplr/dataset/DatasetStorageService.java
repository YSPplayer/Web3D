package com.deeplr.dataset;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Service;

@Service //Spring自动创建这个类
public class DatasetStorageService implements InitializingBean {

  private final DatasetStorageProperties properties;

  public DatasetStorageService(DatasetStorageProperties properties) {
    this.properties = properties;
  }

  @Override
  public void afterPropertiesSet() {
    createDirectory(rootDir());
    createDirectory(syntheticDigitRootDir());
  }

  public Path rootDir() {
    return properties.getRootDir().toAbsolutePath().normalize();
  }

  public Path syntheticDigitRootDir() {
    return rootDir().resolve("datasets").resolve("synthetic-digits");
  }

  private void createDirectory(Path path) {
    try {
      Files.createDirectories(path);
    } catch (IOException error) {
      throw new UncheckedIOException("Failed to create dataset directory: " + path, error);
    }
  }
}
