package com.deeplr.dataset;

import java.nio.file.Path;

public class SyntheticDigitGenerateResult {

  private final String batchId;
  private final Path outputDir;
  private final Path imagesDir;
  private final int count;
  private final int width;
  private final int height;
  private final double noiseLevel;
  private final int digitsPerImage;

  public SyntheticDigitGenerateResult(
      String batchId,
      Path outputDir,
      Path imagesDir,
      int count,
      int width,
      int height,
      double noiseLevel,
      int digitsPerImage) {
    this.batchId = batchId;
    this.outputDir = outputDir;
    this.imagesDir = imagesDir;
    this.count = count;
    this.width = width;
    this.height = height;
    this.noiseLevel = noiseLevel;
    this.digitsPerImage = digitsPerImage;
  }

  public String getBatchId() {
    return batchId;
  }

  public Path getOutputDir() {
    return outputDir;
  }

  public Path getImagesDir() {
    return imagesDir;
  }

  public int getCount() {
    return count;
  }

  public int getWidth() {
    return width;
  }

  public int getHeight() {
    return height;
  }

  public double getNoiseLevel() {
    return noiseLevel;
  }

  public int getDigitsPerImage() {
    return digitsPerImage;
  }
}
