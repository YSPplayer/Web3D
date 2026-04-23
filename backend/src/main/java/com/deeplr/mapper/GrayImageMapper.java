package com.deeplr.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;

import com.deeplr.entity.GrayImage;
@Mapper
public interface GrayImageMapper {
    /*
    插入单个数据库的数据
    */
    @Insert("INSERT INTO gray_image (img_key, img_path,img_value,width,height,interference_strength,img_status) VALUES (#{imgKey}, #{imgPath}, #{imgValue}, #{width}, #{height}, #{interferenceStrength}, #{imgStatus})")
    @Options(useGeneratedKeys = true, keyProperty = "id", keyColumn = "id")
    int insert(GrayImage grayImage);

     /**
     * 批量插入
     */
    int insertBatch(@Param("list") List<GrayImage> list);
}
