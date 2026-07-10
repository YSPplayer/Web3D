package com.deeplr.config;

import java.nio.file.Path;
import java.nio.file.Paths;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.deeplr.dataset.DatasetStorageProperties;

@Configuration
public class StaticResourceConfig implements WebMvcConfigurer {

    private static final String PUBLIC_PATH_PATTERN = "/dataset-files/**";

    private final DatasetStorageProperties datasetStorageProperties;

    public StaticResourceConfig(DatasetStorageProperties datasetStorageProperties) {
        this.datasetStorageProperties = datasetStorageProperties;
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        Path rootDir = Paths.get(datasetStorageProperties.getRootDir()).toAbsolutePath().normalize();
        String location = rootDir.toUri().toString();
        if (!location.endsWith("/")) {
            location = location + "/";
        }
        registry.addResourceHandler(PUBLIC_PATH_PATTERN)
                .addResourceLocations(location);
    }
}
