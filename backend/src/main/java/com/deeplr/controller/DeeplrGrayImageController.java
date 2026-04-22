package com.deeplr.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMethod;

import com.deeplr.dataset.SyntheticDigitDatasetService;
import com.deeplr.dataset.SyntheticDigitGenerateRequest;

@RestController
public class DeeplrGrayImageController {
    private final SyntheticDigitDatasetService syntheticDigitDatasetService;

    public DeeplrGrayImageController(SyntheticDigitDatasetService syntheticDigitDatasetService) {
        this.syntheticDigitDatasetService = syntheticDigitDatasetService;
    }

    //批量生成样本数据
    @RequestMapping(value = "/generateGrayDatas",method = RequestMethod.GET)
    public void generateGrayDatas(int count) {
        SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest(); 
        request.setCount(count);
        request.setWidth(160);
        request.setHeight(64);
        request.setDigitsPerImage(4);
        request.setNoiseLevel(0.2);
        syntheticDigitDatasetService.generate(request);
    }   
}
