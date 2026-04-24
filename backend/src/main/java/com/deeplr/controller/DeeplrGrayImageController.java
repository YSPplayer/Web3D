package com.deeplr.controller;

import java.util.List;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import com.deeplr.common.ApiResponse;
import com.deeplr.entity.GrayImage;
import com.deeplr.service.GrayImageService;

@RestController
public class DeeplrGrayImageController {

    private final GrayImageService grayImageService;

    public DeeplrGrayImageController(GrayImageService grayImageService) {
        this.grayImageService = grayImageService;
    }

    @RequestMapping(value = "/grayImage/generateGrayDatas", method = RequestMethod.GET)
    public ApiResponse<List<GrayImage>> generateGrayDatas(int count) {
        return ApiResponse.success(grayImageService.generateDefaultGrayImages(count));
    }
}
