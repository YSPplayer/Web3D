# DeepLR Backend

Spring Boot backend for the DeepLR neural network learning project.

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

The backend creates dataset folders under `DEEPLR_DATA_DIR`.

If the environment variable is not set, it defaults to:

```text
${user.home}/Deeplr-data
```

Current synthetic digit dataset folder:

```text
Deeplr-data/
  datasets/
    synthetic-digits/
```
