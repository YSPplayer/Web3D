package com.deeplr.dataset;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class SyntheticDigitDatasetServiceTests {

  @TempDir
  Path tempDir;

  @Test
  void generateCreatesImagesWithoutLabelsFile() throws IOException {
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService());
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setBatchId("test-batch");
    request.setCount(5);
    request.setWidth(32);
    request.setHeight(32);
    request.setNoiseLevel(0.25);
    request.setSeed(123L);

    SyntheticDigitGenerateResult result = service.generate(request);

    assertEquals("test-batch", result.getBatchId());
    assertEquals(1, result.getDigitsPerImage());
    assertTrue(Files.isDirectory(result.getImagesDir()));
    assertTrue(Files.notExists(result.getOutputDir().resolve("labels.csv")));

    List<Path> imageFiles = listPngFiles(result.getImagesDir());
    assertEquals(5, imageFiles.size());

    Set<String> filenames = imageFiles.stream()
        .map(path -> path.getFileName().toString())
        .collect(Collectors.toSet());
    assertEquals(5, filenames.size());

    for (Path imageFile : imageFiles) {
      String filename = imageFile.getFileName().toString();
      assertTrue(filename.startsWith("test-batch_"));
      assertTrue(filename.endsWith(".png"));
      assertTrue(Files.isRegularFile(imageFile));

      BufferedImage image = ImageIO.read(imageFile.toFile());
      assertEquals(32, image.getWidth());
      assertEquals(32, image.getHeight());
      assertImageHasContrast(image);
    }
  }

  @Test
  void generateCreatesMultiDigitImagesWithoutLabelsFile() throws IOException {
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService());
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setBatchId("six-digit-batch");
    request.setCount(3);
    request.setWidth(192);
    request.setHeight(64);
    request.setNoiseLevel(0.35);
    request.setDigitsPerImage(6);
    request.setSeed(456L);

    SyntheticDigitGenerateResult result = service.generate(request);

    assertEquals(6, result.getDigitsPerImage());
    assertTrue(Files.notExists(result.getOutputDir().resolve("labels.csv")));

    List<Path> imageFiles = listPngFiles(result.getImagesDir());
    assertEquals(3, imageFiles.size());

    for (Path imageFile : imageFiles) {
      String filename = imageFile.getFileName().toString();
      assertTrue(filename.startsWith("six-digit-batch_"));
      assertTrue(filename.endsWith(".png"));

      BufferedImage image = ImageIO.read(imageFile.toFile());
      assertEquals(192, image.getWidth());
      assertEquals(64, image.getHeight());
      assertImageHasContrast(image);
    }
  }

  @Test
  void generateRejectsUnsafeBatchId() {
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService());
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setBatchId("../bad");

    assertThrows(IllegalArgumentException.class, () -> service.generate(request));
  }

  @Test
  void generateRejectsUnsupportedDigitCount() {
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService());
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setDigitsPerImage(7);

    assertThrows(IllegalArgumentException.class, () -> service.generate(request));
  }

  private DatasetStorageService storageService() {
    DatasetStorageProperties properties = new DatasetStorageProperties();
    properties.setRootDir(tempDir);
    DatasetStorageService storageService = new DatasetStorageService(properties);
    storageService.afterPropertiesSet();
    return storageService;
  }

  private List<Path> listPngFiles(Path directory) throws IOException {
    try (java.util.stream.Stream<Path> stream = Files.list(directory)) {
      return stream
          .filter(path -> Files.isRegularFile(path) && path.getFileName().toString().endsWith(".png"))
          .collect(Collectors.toList());
    }
  }

  private void assertImageHasContrast(BufferedImage image) {
    int min = 255;
    int max = 0;
    for (int y = 0; y < image.getHeight(); y++) {
      for (int x = 0; x < image.getWidth(); x++) {
        int sample = image.getRaster().getSample(x, y, 0);
        min = Math.min(min, sample);
        max = Math.max(max, sample);
      }
    }
    assertNotEquals(min, max);
  }
}
