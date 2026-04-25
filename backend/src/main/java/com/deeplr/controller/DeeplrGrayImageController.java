package com.deeplr.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.deeplr.common.ApiResponse;
import com.deeplr.entity.GrayImage;
import com.deeplr.dataset.SyntheticDigitGenerateRequest;
import com.deeplr.service.GrayImageService;

@RestController
public class DeeplrGrayImageController {

    private final GrayImageService grayImageService;

    public DeeplrGrayImageController(GrayImageService grayImageService) {
        this.grayImageService = grayImageService;
    }
    //后台生成样本，返回生成的样本列表
    @PostMapping("/grayImage/generateGrayDatas")
    public ApiResponse<List<GrayImage>> generateGrayDatas(@RequestBody SyntheticDigitGenerateRequest request) {
        return ApiResponse.success(grayImageService.generateDefaultGrayImages(request.getCount()));
    }

    //分页查询样本列表，返回当前页的样本列表
    @GetMapping("/grayImage/getGrayDatasByPage")
    public ApiResponse<List<GrayImage>> getGrayDatasByPage(int pageNum, int pageSize) {
        return ApiResponse.success(grayImageService.getAllGrayImagesByPage(pageNum, pageSize));
    }
    //查询样本总数量，返回总数量
    @GetMapping("/grayImage/getGrayDataTotalCount")
    public ApiResponse<Integer> getGrayDataTotalCount() {
        return ApiResponse.success(grayImageService.getAllGrayImagesCount());
    }
}