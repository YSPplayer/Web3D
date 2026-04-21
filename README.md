# Web3D Learning Lab

这个仓库现在分成三个独立部分：

- `src/`: Vue/Vite 前端工程
- `backend/`: Java Spring Boot 后端工程
- `native/`: 独立 CMake/C++ 模块

## Frontend

```bash
npm install
npm run dev
```

生产构建：

```bash
npm run build
```

## Backend

后端是独立 Spring Boot 工程，入口在 `backend/`。当前机器没有全局 Maven，所以项目内置了 Maven Wrapper。

```bash
cd backend
.\mvnw.cmd spring-boot:run
```

验证：

```bash
cd backend
.\mvnw.cmd test
```

当前接口：

- `GET http://localhost:8080/api/health`
- `GET http://localhost:8080/api/datasets/storage`

数据集目录默认使用：

```text
${user.home}/Web3D-data
```

也可以通过环境变量覆盖：

```text
WEB3D_DATA_DIR=D:/YueShaoPu/Web3D-data
```

## Native C++

C++ 模块是独立 CMake 工程，入口在 `native/CMakeLists.txt`。

```bash
cmake -S native -B native/build
cmake --build native/build
```

默认目标：

- `web3d_native`: 静态库
- `web3d_native_sandbox`: 示例程序
