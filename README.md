# Filament Tauri Lab

一个用于学习 `Tauri + Rust + Web + Filament` 的最小实验项目。

当前项目已经完成这些基础设施：

- `Tauri 2` 桌面壳子
- `Vite + TypeScript` 前端开发环境
- 一个可直接替换为 Filament 渲染逻辑的前端舞台区域
- 一个最小 Rust `invoke` 示例，确认前后端调用链正常

## 启动

先安装依赖：

```bash
npm install
```

开发模式运行桌面应用：

```bash
npm run tauri dev
```

如果你只想先看前端页面：

```bash
npm run dev
```

生产构建：

```bash
npm run tauri build
```

## 项目结构

- `src/main.ts`: 前端入口，后续可直接初始化 Filament
- `src/styles.css`: 当前实验壳子的样式
- `index.html`: 页面骨架，包含 `#filament-stage` 挂载点
- `src-tauri/src/lib.rs`: Rust 端命令入口
- `src-tauri/tauri.conf.json`: 窗口和构建配置

## 你接 Filament 的位置

推荐从这一步开始：

1. 在 `src/main.ts` 中引入 Filament 的 JS/Wasm 资源
2. 把 Filament 创建出来的 `canvas` 挂到 `#filament-stage`
3. 保持渲染逻辑在前端
4. 把计算密集、工具型、文件处理型逻辑逐步迁到 Rust 命令

## 建议学习路线

第一阶段：

- 跑通 Tauri 壳子
- 在前端区域挂一个普通 `canvas`
- 学会用 JS 控制视口、输入、动画循环

第二阶段：

- 接入 Filament Web
- 加载 glTF 或简单几何
- 做材质和相机实验

第三阶段：

- 用 Rust 提供配置读取、资源索引、模型处理、数学计算或场景逻辑
- 再通过 Tauri `invoke` 与前端交互

## 推荐开发环境

- VS Code
- `rust-analyzer`
- `Tauri` VS Code 插件
