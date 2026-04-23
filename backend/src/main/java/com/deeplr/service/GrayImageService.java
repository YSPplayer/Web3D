package com.deeplr.service;

import java.util.List;

import org.springframework.stereotype.Service;

import com.deeplr.dataset.SyntheticDigitDatasetService;
import com.deeplr.dataset.SyntheticDigitGenerateRequest;
import com.deeplr.entity.GrayImage;
import com.deeplr.mapper.GrayImageMapper;

@Service
public class GrayImageService {
        private final SyntheticDigitDatasetService syntheticDigitDatasetService;
        private final GrayImageMapper grayImageMapper;

        public GrayImageService(SyntheticDigitDatasetService syntheticDigitDatasetService, GrayImageMapper grayImageMapper) {
            this.syntheticDigitDatasetService = syntheticDigitDatasetService;
            this.grayImageMapper = grayImageMapper;
        }
        //批量生成样本数据
        public List<GrayImage> generateDefaultGrayImages(int count) {
            SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
            request.setCount(count);
            request.setWidth(160);
            request.setHeight(64);
            request.setDigitsPerImage(4);
            request.setNoiseLevel(0.2);
            List<GrayImage> images = syntheticDigitDatasetService.generate(request);
            //入数据库
            if(!images.isEmpty()) {
                grayImageMapper.insertBatch(images);
            }
            return images;
        }

}
