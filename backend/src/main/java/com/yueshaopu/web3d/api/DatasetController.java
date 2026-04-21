package com.yueshaopu.web3d.api;

import com.yueshaopu.web3d.dataset.DatasetStorageService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/datasets")
public class DatasetController {

  private final DatasetStorageService datasetStorageService;

  public DatasetController(DatasetStorageService datasetStorageService) {
    this.datasetStorageService = datasetStorageService;
  }

  @GetMapping("/storage")
  public Map<String, String> storage() {
    return datasetStorageService.describe();
  }
}
