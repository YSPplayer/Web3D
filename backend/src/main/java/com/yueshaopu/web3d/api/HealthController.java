package com.yueshaopu.web3d.api;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

  @GetMapping("/api/health")
  public Map<String, Object> health() {
    Map<String, Object> response = new LinkedHashMap<String, Object>();
    response.put("status", "ok");
    response.put("service", "web3d-backend");
    response.put("timestamp", Instant.now().toString());
    return response;
  }
}
