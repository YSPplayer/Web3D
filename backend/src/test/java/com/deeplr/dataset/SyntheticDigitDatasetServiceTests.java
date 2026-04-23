package com.deeplr.dataset;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import javax.imageio.ImageIO;
import com.deeplr.entity.GrayImage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class SyntheticDigitDatasetServiceTests {

  @TempDir
  Path tempDir;

  @Test
  void generateCreatesImagesWithoutLabelsFile() throws IOException {
    DatasetStorageService storageService = storageService();
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService);
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setBatchId("test-batch");
    request.setCount(5);
    request.setWidth(32);
    request.setHeight(32);
    request.setNoiseLevel(0.25);
    request.setSeed(123L);

    List<GrayImage> result = service.generate(request);
    Path outputDir = storageService.syntheticDigitRootDir().resolve("test-batch").normalize();
    Path imagesDir = outputDir.resolve("images");

    assertTrue(Files.isDirectory(imagesDir));
    assertTrue(Files.notExists(outputDir.resolve("labels.csv")));
    assertEquals(5, result.size());

    Set<String> imgKeys = result.stream()
        .map(GrayImage::getImgKey)
        .collect(Collectors.toSet());
    assertEquals(5, imgKeys.size());

    for (GrayImage grayImage : result) {
      Path imageFile = Paths.get(grayImage.getImgPath());
      String filename = imageFile.getFileName().toString();
      assertTrue(grayImage.getImgKey().startsWith("test-batch_"));
      assertTrue(filename.startsWith("test-batch_"));
      assertTrue(filename.endsWith(".png"));
      assertEquals(grayImage.getImgKey() + ".png", filename);
      assertEquals(Integer.valueOf(32), grayImage.getWidth());
      assertEquals(Integer.valueOf(32), grayImage.getHeight());
      assertEquals(BigDecimal.valueOf(0.25), grayImage.getInterferenceStrength());
      assertEquals(Long.valueOf(0L), grayImage.getImgStatus());
      assertTrue(Files.isRegularFile(imageFile));

      BufferedImage image = ImageIO.read(imageFile.toFile());
      assertEquals(32, image.getWidth());
      assertEquals(32, image.getHeight());
      assertImageHasContrast(image);
    }
  }

  @Test
  void generateCreatesMultiDigitImagesWithoutLabelsFile() throws IOException {
    DatasetStorageService storageService = storageService();
    SyntheticDigitDatasetService service = new SyntheticDigitDatasetService(storageService);
    SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
    request.setBatchId("six-digit-batch");
    request.setCount(3);
    request.setWidth(192);
    request.setHeight(64);
    request.setNoiseLevel(0.35);
    request.setDigitsPerImage(6);
    request.setSeed(456L);

    List<GrayImage> result = service.generate(request);
    Path outputDir = storageService.syntheticDigitRootDir().resolve("six-digit-batch").normalize();

    assertTrue(Files.notExists(outputDir.resolve("labels.csv")));
    assertEquals(3, result.size());

    for (GrayImage grayImage : result) {
      Path imageFile = Paths.get(grayImage.getImgPath());
      String filename = imageFile.getFileName().toString();
      assertTrue(grayImage.getImgKey().startsWith("six-digit-batch_"));
      assertTrue(filename.startsWith("six-digit-batch_"));
      assertTrue(filename.endsWith(".png"));
      assertEquals(grayImage.getImgKey() + ".png", filename);
      assertEquals(Integer.valueOf(192), grayImage.getWidth());
      assertEquals(Integer.valueOf(64), grayImage.getHeight());
      assertEquals(BigDecimal.valueOf(0.35), grayImage.getInterferenceStrength());
      assertEquals(Long.valueOf(0L), grayImage.getImgStatus());

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
