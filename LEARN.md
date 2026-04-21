# 启动与学习说明

当前仓库分成三块：

- 根目录：Vue/Vite 前端工程
- `backend/`：Java Spring Boot 后端工程
- `native/`：独立 CMake/C++ 工程

## 运行前端

```bash
npm install
npm run dev
```

## 运行后端

```bash
cd backend
.\mvnw.cmd spring-boot:run
```

后端会自动创建数据集目录：

```text
Web3D-data/
  datasets/
    mnist/
      raw/
      processed/
      previews/
```

查看后端状态：

```text
GET http://localhost:8080/api/health
```

查看数据集目录：

```text
GET http://localhost:8080/api/datasets/storage
```

## 构建 C++ 模块

```bash
cmake -S native -B native/build
cmake --build native/build
```

## 建议接入顺序

1. 先用后端下载或导入 MNIST 原始数据到 `raw/`。
2. 后端把 IDX 数据解析成训练输入和预览图片。
3. 前端展示样本、标签分布、训练曲线和预测结果。
4. 后端逐步实现展平输入、全连接层、激活函数、损失函数和反向传播。
