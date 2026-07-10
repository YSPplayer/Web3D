package com.deeplr.dataset;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.awt.image.ConvolveOp;
import java.awt.image.Kernel;
import java.awt.image.WritableRaster;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import javax.imageio.ImageIO;
import com.deeplr.entity.GrayImage;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class SyntheticDigitDatasetService {

  private static final String PUBLIC_IMAGE_PREFIX = "/dataset-files/";
  private static final DateTimeFormatter BATCH_TIME_FORMATTER =
      DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
  private static final Font[] DIGIT_FONTS = new Font[] {
      new Font(Font.SANS_SERIF, Font.BOLD, 1),
      new Font(Font.SERIF, Font.BOLD, 1),
      new Font(Font.MONOSPACED, Font.BOLD, 1)
  };

  private final DatasetStorageService datasetStorageService;

  public SyntheticDigitDatasetService(DatasetStorageService datasetStorageService) {
    this.datasetStorageService = datasetStorageService;
  }

  public List<GrayImage> generate(SyntheticDigitGenerateRequest request) {
    SyntheticDigitGenerateRequest normalized = normalize(request);
    Random random = normalized.getSeed() == null ? new Random() : new Random(normalized.getSeed());
    String batchId = resolveBatchId(normalized);
    Path outputDir = datasetStorageService.syntheticDigitRootDir().resolve(batchId).normalize();
    Path imagesDir = outputDir.resolve("images");

    try {
      Files.createDirectories(imagesDir);
      return writeImages(normalized, random, batchId, imagesDir);
    } catch (IOException error) {
      throw new UncheckedIOException("Failed to generate synthetic digit dataset: " + outputDir, error);
    }
  }

  BufferedImage createDigitImage(
      String label, int width, int height, double noiseLevel, Random random) {
    BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_BYTE_GRAY);
    Graphics2D graphics = image.createGraphics();
    try {
      graphics.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
      graphics.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

      fillBackground(image, random);
      drawInterferenceLines(graphics, width, height, noiseLevel, label.length(), random);
      drawDigits(graphics, label, width, height, random);
    } finally {
      graphics.dispose();
    }

    addPixelNoise(image, noiseLevel, random);
    return maybeBlur(image, random);
  }

  private List<GrayImage> writeImages(
      SyntheticDigitGenerateRequest request,
      Random random,
      String batchId,
      Path imagesDir)
      throws IOException {
    List<GrayImage> grayImages = new ArrayList<>(request.getCount());
    LocalDateTime createdAt = LocalDateTime.now();
    for (int index = 1; index <= request.getCount(); index++) {
      String label = randomDigitText(request.getDigitsPerImage(), random);
      String filename = createUniqueFilename(batchId);
      BufferedImage image = createDigitImage(
          label,
          request.getWidth(),
          request.getHeight(),
          request.getNoiseLevel(),
          random);
      Path imageFile = imagesDir.resolve(filename);
      if (!ImageIO.write(image, "png", imageFile.toFile())) {
        throw new IOException("No ImageIO writer found for png");
      }
      grayImages.add(createGrayImage(request, label, filename, imageFile, createdAt));
    }
    return grayImages;
  }

  private String createUniqueFilename(String batchId) {
    return batchId + "_" + UUID.randomUUID().toString().replace("-", "") + ".png";
  }

  private GrayImage createGrayImage(
      SyntheticDigitGenerateRequest request,
      String label,
      String filename,
      Path imageFile,
      LocalDateTime createdAt) {
    String imgKey = filename.substring(0, filename.length() - ".png".length());
    GrayImage grayImage = new GrayImage();
    grayImage.setImgKey(imgKey);
    grayImage.setImgPath(buildPublicImagePath(imageFile));
    grayImage.setImgValue(label);
    grayImage.setWidth(request.getWidth());
    grayImage.setHeight(request.getHeight());
    grayImage.setInterferenceStrength(BigDecimal.valueOf(request.getNoiseLevel()));
    grayImage.setImgStatus(0L);
    grayImage.setCreateTime(createdAt);
    return grayImage;
  }

  private SyntheticDigitGenerateRequest normalize(SyntheticDigitGenerateRequest request) {
    SyntheticDigitGenerateRequest source = request == null ? new SyntheticDigitGenerateRequest() : request;
    if (source.getCount() < 1) {
      throw new IllegalArgumentException("count must be greater than 0");
    }
    if (source.getWidth() < 16 || source.getHeight() < 16) {
      throw new IllegalArgumentException("width and height must be at least 16");
    }
    if (source.getDigitsPerImage() < 1 || source.getDigitsPerImage() > 6) {
      throw new IllegalArgumentException("digitsPerImage must be between 1 and 6");
    }
    if (source.getWidth() < source.getDigitsPerImage() * 18) {
      throw new IllegalArgumentException("width is too small for digitsPerImage");
    }
    if (source.getNoiseLevel() < 0.0 || source.getNoiseLevel() > 1.0) {
      throw new IllegalArgumentException("noiseLevel must be between 0 and 1");
    }
    if (StringUtils.hasText(source.getBatchId())
        && !source.getBatchId().matches("[A-Za-z0-9_-]+")) {
      throw new IllegalArgumentException("batchId may only contain letters, numbers, underscores and hyphens");
    }
    return source;
  }

  private String resolveBatchId(SyntheticDigitGenerateRequest request) {
    if (StringUtils.hasText(request.getBatchId())) {
      return request.getBatchId();
    }
    String timestamp = LocalDateTime.now().format(BATCH_TIME_FORMATTER);
    String suffix = UUID.randomUUID().toString().substring(0, 8);
    return timestamp + "-" + suffix;
  }

  private String buildPublicImagePath(Path imageFile) {
    Path relativePath = datasetStorageService.rootDir()
        .relativize(imageFile.toAbsolutePath().normalize());
    return PUBLIC_IMAGE_PREFIX + relativePath.toString().replace("\\", "/");
  }

  private String randomDigitText(int digitsPerImage, Random random) {
    StringBuilder text = new StringBuilder(digitsPerImage);
    for (int index = 0; index < digitsPerImage; index++) {
      text.append(random.nextInt(10));
    }
    return text.toString();
  }

  private void fillBackground(BufferedImage image, Random random) {
    WritableRaster raster = image.getRaster();
    int width = image.getWidth();
    int height = image.getHeight();
    int baseGray = randomInt(random, 218, 248);
    for (int y = 0; y < height; y++) {
      for (int x = 0; x < width; x++) {
        raster.setSample(x, y, 0, clamp(baseGray + randomInt(random, -6, 6)));
      }
    }
  }

  private void drawInterferenceLines(
      Graphics2D graphics,
      int width,
      int height,
      double noiseLevel,
      int digitsPerImage,
      Random random) {
    int lineCount = 1 + digitsPerImage + (int) Math.round(noiseLevel * 10.0);
    for (int index = 0; index < lineCount; index++) {
      int gray = randomInt(random, 80, 190);
      graphics.setColor(new Color(gray, gray, gray));
      graphics.setStroke(new BasicStroke((float) randomDouble(random, 0.6, 1.8)));
      int x1 = randomInt(random, -width / 4, width);
      int y1 = randomInt(random, 0, height);
      int x2 = randomInt(random, 0, width + width / 4);
      int y2 = randomInt(random, 0, height);
      graphics.drawLine(x1, y1, x2, y2);
    }
  }

  private void drawDigits(Graphics2D graphics, String label, int width, int height, Random random) {
    double cellWidth = width / (double) label.length();
    for (int index = 0; index < label.length(); index++) {
      double cellLeft = index * cellWidth;
      drawSingleDigit(graphics, label.charAt(index), cellLeft, cellWidth, height, random);
    }
  }

  private void drawSingleDigit(
      Graphics2D graphics,
      char digit,
      double cellLeft,
      double cellWidth,
      int height,
      Random random) {
    int minSide = (int) Math.min(cellWidth, height);
    int minFontSize = Math.max(10, (int) (minSide * 0.58));
    int maxFontSize = Math.max(minFontSize, (int) (minSide * 0.82));
    int fontSize = randomInt(random, minFontSize, maxFontSize);
    Font baseFont = DIGIT_FONTS[random.nextInt(DIGIT_FONTS.length)];
    Font font = baseFont.deriveFont((float) fontSize);
    String text = Character.toString(digit);

    graphics.setFont(font);
    FontMetrics metrics = graphics.getFontMetrics();
    int textWidth = metrics.stringWidth(text);
    int textHeight = metrics.getAscent() - metrics.getDescent();
    double centerX = cellLeft + cellWidth / 2.0;
    double centerY = height / 2.0;
    double x = centerX - textWidth / 2.0 + randomDouble(random, -cellWidth * 0.08, cellWidth * 0.08);
    double y = (height + textHeight) / 2.0 + randomDouble(random, -height * 0.08, height * 0.08);

    AffineTransform originalTransform = graphics.getTransform();
    AffineTransform transform = new AffineTransform();
    transform.translate(centerX, centerY);
    transform.rotate(Math.toRadians(randomDouble(random, -16.0, 16.0)));
    transform.scale(randomDouble(random, 0.88, 1.12), randomDouble(random, 0.88, 1.12));
    transform.translate(-centerX, -centerY);
    graphics.transform(transform);

    int digitGray = randomInt(random, 8, 70);
    graphics.setColor(new Color(digitGray, digitGray, digitGray));
    graphics.drawString(text, (float) x, (float) y);
    graphics.setTransform(originalTransform);
  }

  private void addPixelNoise(BufferedImage image, double noiseLevel, Random random) {
    WritableRaster raster = image.getRaster();
    int width = image.getWidth();
    int height = image.getHeight();
    int changedPixels = (int) Math.round(width * height * noiseLevel * 0.08);
    for (int index = 0; index < changedPixels; index++) {
      int x = random.nextInt(width);
      int y = random.nextInt(height);
      int gray = random.nextBoolean()
          ? randomInt(random, 0, 70)
          : randomInt(random, 185, 255);
      raster.setSample(x, y, 0, gray);
    }
  }

  private BufferedImage maybeBlur(BufferedImage image, Random random) {
    if (random.nextDouble() > 0.35) {
      return image;
    }
    float[] kernelValues = new float[] {
        0.05f, 0.10f, 0.05f,
        0.10f, 0.40f, 0.10f,
        0.05f, 0.10f, 0.05f
    };
    ConvolveOp operation = new ConvolveOp(new Kernel(3, 3, kernelValues), ConvolveOp.EDGE_NO_OP, null);
    BufferedImage blurred = new BufferedImage(
        image.getWidth(),
        image.getHeight(),
        BufferedImage.TYPE_BYTE_GRAY);
    operation.filter(image, blurred);
    return blurred;
  }

  private int randomInt(Random random, int minInclusive, int maxInclusive) {
    if (maxInclusive <= minInclusive) {
      return minInclusive;
    }
    return minInclusive + random.nextInt(maxInclusive - minInclusive + 1);
  }

  private double randomDouble(Random random, double minInclusive, double maxInclusive) {
    return minInclusive + random.nextDouble() * (maxInclusive - minInclusive);
  }

  private int clamp(int value) {
    return Math.max(0, Math.min(255, value));
  }
}
