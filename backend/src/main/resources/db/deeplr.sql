CREATE DATABASE IF NOT EXISTS deeplr_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE deeplr_db;
CREATE TABLE IF NOT EXISTS gray_image (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    img_key VARCHAR(500) NOT NULL COMMENT '图片键',
    img_path VARCHAR(500) NOT NULL COMMENT '图片路径',
    img_value VARCHAR(8) NOT NULL COMMENT '图片值',
    width INT NOT NULL COMMENT '图片宽度',
    height INT NOT NULL COMMENT '图片高度',
    interference_strength DECIMAL(5,2) NOT NULL COMMENT '干扰强度',
    img_status BIGINT NOT NULL COMMENT '特殊标签', 
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_create_time (create_time),
    INDEX idx_img_key (img_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='灰度图像数据表';