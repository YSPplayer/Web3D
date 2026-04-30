package com.deeplr.service;

import java.util.List;

import org.omg.CORBA.PUBLIC_MEMBER;
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
        request.setWidth(128);
        request.setHeight(128);
        request.setDigitsPerImage(4);
        request.setNoiseLevel(0.2);
        List<GrayImage> images = syntheticDigitDatasetService.generate(request);
        if (!images.isEmpty()) {
            grayImageMapper.insertBatch(images);
        }
        return formatImages(images);
    }
    private List<GrayImage> formatImages(List<GrayImage> images) {
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

    public List<GrayImage> getAllGrayImagesByPage(int pageNum,int pageSzie) {
        if (pageNum <= 0 || pageSzie <= 0) {
            throw new IllegalArgumentException("分页参数不合法: pageNum=" + pageNum + ", pageSize=" + pageSzie);
        }
        int offset = (pageNum - 1) * pageSzie;
        return formatImages(grayImageMapper.selectAllByPage(offset, pageSzie));
    }

    public Integer getAllGrayImagesCount() {
        return grayImageMapper.selectAllCount();
    }
}
