package com.deeplr.controller;

import java.util.List;

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

    @PostMapping("/grayImage/generateGrayDatas")
    public ApiResponse<List<GrayImage>> generateGrayDatas(@RequestBody SyntheticDigitGenerateRequest request) {
        return ApiResponse.success(grayImageService.generateDefaultGrayImages(request.getCount()));
    }
}
