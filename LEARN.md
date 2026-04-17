# 启动与学习说明

## 这是什么

这是一个给你学习下面几件事的实验壳子：

- Tauri 桌面应用结构
- Rust 与前端的交互方式
- 用 Vite 管理 Web 侧代码
- 后续接入 Filament Web 渲染

## 启动方法

在项目根目录执行：

```bash
npm install
npm run tauri dev
```

如果启动成功，你会看到一个桌面窗口，左侧有 `Ping Rust` 按钮，右侧是一个预留给 3D 渲染的区域。

点击 `Ping Rust` 后，如果文案变成 `Rust bridge online`，说明：

- 前端 Vite 正常
- Tauri 壳子正常
- Rust 命令调用正常

## 只运行前端

```bash
npm run dev
```

然后在浏览器打开 Vite 输出的本地地址。

这个模式适合你先调页面结构和 Filament 初始化脚本。

## 生产构建

```bash
npm run tauri build
```

打包产物会出现在 Tauri 默认构建目录下。

## 从哪里开始接 Filament

最直接的做法是改这两个地方：

- `index.html`
- `src/main.ts`

当前已经给你留了一个挂载区域：

```html
<div id="filament-stage" class="stage"></div>
```

你后续可以：

1. 创建 `canvas`
2. 挂到 `#filament-stage`
3. 初始化 Filament engine / scene / camera
4. 把交互逻辑继续放在前端

## Rust 在这里适合做什么

建议先不要让 Rust 直接接管 Filament 渲染层。

更合理的职责分工是：

- JS/TS: Filament 初始化、canvas、渲染循环、材质和场景绑定
- Rust: 配置、资源管理、几何计算、模型预处理、场景逻辑、工具命令

## 你接下来最值得做的第一步

把一个普通 `canvas` 放进 `#filament-stage`，先验证：

- 尺寸自适应
- 鼠标输入
- 每帧刷新

然后再替换成 Filament。
