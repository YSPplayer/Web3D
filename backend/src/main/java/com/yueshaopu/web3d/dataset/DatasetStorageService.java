package com.yueshaopu.web3d.dataset;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Service;

@Service
public class DatasetStorageService implements InitializingBean {

  private final DatasetStorageProperties properties;

  public DatasetStorageService(DatasetStorageProperties properties) {
    this.properties = properties;
  }

  @Override
  public void afterPropertiesSet() {
    createDirectory(rootDir());
    createDirectory(mnistRawDir());
    createDirectory(mnistProcessedDir());
    createDirectory(mnistPreviewDir());
  }

  public Map<String, String> describe() {
    Map<String, String> paths = new LinkedHashMap<String, String>();
    paths.put("rootDir", rootDir().toString());
    paths.put("mnistRawDir", mnistRawDir().toString());
    paths.put("mnistProcessedDir", mnistProcessedDir().toString());
    paths.put("mnistPreviewDir", mnistPreviewDir().toString());
    return paths;
  }

  private Path rootDir() {
    return properties.getRootDir().toAbsolutePath().normalize();
  }

  private Path mnistRawDir() {
    return rootDir().resolve("datasets").resolve("mnist").resolve("raw");
  }

  private Path mnistProcessedDir() {
    return rootDir().resolve("datasets").resolve("mnist").resolve("processed");
  }

  private Path mnistPreviewDir() {
    return rootDir().resolve("datasets").resolve("mnist").resolve("previews");
  }

  private void createDirectory(Path path) {
    try {
      Files.createDirectories(path);
    } catch (IOException error) {
      throw new UncheckedIOException("Failed to create dataset directory: " + path, error);
    }
  }
}
