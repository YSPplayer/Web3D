package com.deeplr.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import com.deeplr.entity.GrayImage;

@Mapper
public interface GrayImageMapper {

    @Insert("INSERT INTO gray_image (img_key, img_path, img_value, width, height, interference_strength, img_status, create_time) "
            + "VALUES (#{imgKey}, #{imgPath}, #{imgValue}, #{width}, #{height}, #{interferenceStrength}, #{imgStatus}, #{createTime})")
    int insert(GrayImage grayImage);
    @Select("SELECT * FROM gray_image LIMIT #{offset}, #{limit}")
    List<GrayImage> selectAllByPage(@Param("offset") int offset, @Param("limit") int limit);
    @Select("SELECT COUNT(*) FROM gray_image")
    int selectAllCount();
    int insertBatch(@Param("list") List<GrayImage> list);
}
