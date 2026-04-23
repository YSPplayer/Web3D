package com.deeplr.config;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@ConfigurationProperties(prefix = "deeplr.cors")
public class CorsConfig implements WebMvcConfigurer {

  private List<String> allowedOrigins = Collections.singletonList("http://localhost:5173");

  public List<String> getAllowedOrigins() {
    return allowedOrigins;
  }

  public void setAllowedOrigins(List<String> allowedOrigins) {
    this.allowedOrigins = allowedOrigins;
  }

  @Override
  public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
        .allowedOrigins(normalizeOrigins().toArray(new String[0]))
        .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
        .allowedHeaders("*");
  }

  private List<String> normalizeOrigins() {
    List<String> origins = new ArrayList<String>();
    for (String origin : allowedOrigins) {
      if (origin == null || origin.trim().isEmpty()) {
        continue;
      }
      origins.add(removeTrailingSlash(origin.trim()));
    }
    return origins;
  }

  private String removeTrailingSlash(String origin) {
    while (origin.endsWith("/")) {
      origin = origin.substring(0, origin.length() - 1);
    }
    return origin;
  }
}
