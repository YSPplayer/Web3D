package com.deeplr.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class GrayImage {
    private Long id;                      // 主键ID
    private String imgKey;                // 图片键
    private String imgPath;               // 图片路径
    private Long imgValue;                // 图片值
    private Integer width;                // 图片宽度
    private Integer height;               // 图片高度
    private BigDecimal interferenceStrength; // 干扰强度
    private Long imgStatus;               // 特殊标签
    private LocalDateTime createTime;     // 创建时间
    // 构造方法
    public GrayImage() {}
    public GrayImage(String imgKey, String imgPath, Long imgValue, 
                     Integer width, Integer height, BigDecimal interferenceStrength, Long imgStatus) {
        this.imgKey = imgKey;
        this.imgPath = imgPath;
        this.imgValue = imgValue;
        this.width = width;
        this.height = height;
        this.interferenceStrength = interferenceStrength;
        this.imgStatus = imgStatus;
    }
    
    // Getter 和 Setter
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
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
    
    public Long getImgValue() {
        return imgValue;
    }
    
    public void setImgValue(Long imgValue) {
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
                "id=" + id +
                ", imgKey='" + imgKey + '\'' +
                ", imgPath='" + imgPath + '\'' +
                ", imgValue=" + imgValue +
                ", width=" + width +
                ", height=" + height +
                ", interferenceStrength=" + interferenceStrength +
                ", imgStatus=" + imgStatus +
                ", createTime=" + createTime +
                '}';
    }
}
