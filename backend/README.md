# Web3D Backend

Spring Boot backend for the Web3D neural network learning project.

## Requirements

- Java 8 or newer

This project includes Maven Wrapper, so global Maven is not required.

## Run

```bash
.\mvnw.cmd spring-boot:run
```

## Test

```bash
.\mvnw.cmd test
```

## Dataset Storage

The backend creates dataset folders under `WEB3D_DATA_DIR`.

If the environment variable is not set, it defaults to:

```text
${user.home}/Web3D-data
```

Current MNIST folders:

```text
Web3D-data/
  datasets/
    mnist/
      raw/
      processed/
      previews/
```

Check storage paths:

```text
GET http://localhost:8080/api/datasets/storage
```
