package com.deeplr.dataset;

public class SyntheticDigitGenerateRequest {

  private int count = 100;
  private int width = 64;
  private int height = 64;
  private double noiseLevel = 0.18;
  private int digitsPerImage = 1;
  private Long seed;
  private String batchId;

  public int getCount() {
    return count;
  }

  public void setCount(int count) {
    this.count = count;
  }

  public int getWidth() {
    return width;
  }

  public void setWidth(int width) {
    this.width = width;
  }

  public int getHeight() {
    return height;
  }

  public void setHeight(int height) {
    this.height = height;
  }

  public double getNoiseLevel() {
    return noiseLevel;
  }

  public void setNoiseLevel(double noiseLevel) {
    this.noiseLevel = noiseLevel;
  }

  public int getDigitsPerImage() {
    return digitsPerImage;
  }

  public void setDigitsPerImage(int digitsPerImage) {
    this.digitsPerImage = digitsPerImage;
  }

  public Long getSeed() {
    return seed;
  }

  public void setSeed(Long seed) {
    this.seed = seed;
  }

  public String getBatchId() {
    return batchId;
  }

  public void setBatchId(String batchId) {
    this.batchId = batchId;
  }
}
