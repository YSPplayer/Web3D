package com.deeplr.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

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

    public List<GrayImage> generateDefaultGrayImages(int count) {
        if (count <= 0 || count > 30) {
            throw new IllegalArgumentException("参数数量不合法: " + count);
        }
        SyntheticDigitGenerateRequest request = new SyntheticDigitGenerateRequest();
        request.setCount(count);
        request.setWidth(160);
        request.setHeight(64);
        request.setDigitsPerImage(4);
        request.setNoiseLevel(0.2);
        List<GrayImage> images = syntheticDigitDatasetService.generate(request);
        if (!images.isEmpty()) {
            grayImageMapper.insertBatch(images);
        }
        for (GrayImage image : images) {
            image.setImgPath(toAbsoluteUrl(image.getImgPath()));
        }
        return images;
    }

    private String toAbsoluteUrl(String path) {
        if (path == null || path.trim().isEmpty()) {
            return path;
        }
        if (path.startsWith("http://") || path.startsWith("https://")) {
            return path;
        }
        return ServletUriComponentsBuilder.fromCurrentContextPath()
                .path(path.startsWith("/") ? path : "/" + path)
                .toUriString();
    }
}
