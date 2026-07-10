package com.deeplr.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class GrayImage {
    private String imgKey;
    private String imgPath;
    private String imgValue;
    private Integer width;
    private Integer height;
    private BigDecimal interferenceStrength;
    private Long imgStatus;
    private LocalDateTime createTime;

    public GrayImage() {}

    public GrayImage(String imgKey, String imgPath, String imgValue,
                     Integer width, Integer height, BigDecimal interferenceStrength, Long imgStatus) {
        this.imgKey = imgKey;
        this.imgPath = imgPath;
        this.imgValue = imgValue;
        this.width = width;
        this.height = height;
        this.interferenceStrength = interferenceStrength;
        this.imgStatus = imgStatus;
    }

    public String getImgKey() {
        return imgKey;
    }

    public void setImgKey(String imgKey) {
        this.imgKey = imgKey;
    }

    public String getImgPath() {
        return imgPath;
    }

    public void setImgPath(String imgPath) {
        this.imgPath = imgPath;
    }

    public String getImgValue() {
        return imgValue;
    }

    public void setImgValue(String imgValue) {
        this.imgValue = imgValue;
    }

    public Integer getWidth() {
        return width;
    }

    public void setWidth(Integer width) {
        this.width = width;
    }

    public Integer getHeight() {
        return height;
    }

    public void setHeight(Integer height) {
        this.height = height;
    }

    public BigDecimal getInterferenceStrength() {
        return interferenceStrength;
    }

    public void setInterferenceStrength(BigDecimal interferenceStrength) {
        this.interferenceStrength = interferenceStrength;
    }

    public Long getImgStatus() {
        return imgStatus;
    }

    public void setImgStatus(Long imgStatus) {
        this.imgStatus = imgStatus;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    @Override
    public String toString() {
        return "GrayImage{" +
                "imgKey='" + imgKey + '\'' +
                ", imgPath='" + imgPath + '\'' +
                ", imgValue='" + imgValue + '\'' +
                ", width=" + width +
                ", height=" + height +
                ", interferenceStrength=" + interferenceStrength +
                ", imgStatus=" + imgStatus +
                ", createTime=" + createTime +
                '}';
    }
}
