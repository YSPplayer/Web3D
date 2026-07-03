# Mini-YOLO From Scratch 学习方案

目标：基于 PyTorch 从零搭建一个小型 YOLO-like 目标检测模型，先理解“输入图片 -> 网格预测 -> box/class/objectness -> loss -> NMS”的完整链路。第一版不追求工业精度，重点是每一层 shape 清楚、loss 可手算、训练流程可调试。

## 1. 学习范围

本阶段要做：

- 用 PyTorch 自己搭建一个小型单尺度目标检测网络。
- 输入一张图片，输出每个物体的类别、位置框和置信度。
- 自己实现 target 构建、检测 loss、预测解码、NMS、可视化验证。
- 先在简单数据集上训练，例如当前项目可生成的数字图片，类别为 `0~9`。

本阶段暂时不做：

- 不复刻完整 YOLOv5/YOLOv8/YOLOv10/YOLO26 工程。
- 不做多尺度检测、不做 anchor 匹配、不做复杂 label assignment。
- 不做实例分割、姿态估计、旋转框。
- 不先追求 mAP 很高，先追求模型能 overfit 小数据。

## 2. 第一版任务定义

推荐第一版使用固定输入：

```text
input image: [B, 3, 256, 256]
class count: C = 10
grid size: S = 8
prediction per cell: 1
output per cell: 4 box + 1 objectness + C class logits = 15
model output: [B, 15, 8, 8]
reshaped output: [B, 8, 8, 15]
```

如果使用当前项目里的灰度数字图，把输入改成：

```text
input image: [B, 1, 256, 256]
```

除了第一层卷积的输入通道从 `3` 改成 `1`，其余 shape 不变。

## 3. 为什么先做单尺度 8x8

YOLO 的核心不是“模型很大”，而是这件事：

```text
把图片划分成 S x S 个网格。
每个网格负责预测中心点落在该网格内的物体。
每个网格输出 box、objectness、class。
```

第一版用 `256x256` 输入，最终特征图是 `8x8`，总 stride 是：

```text
stride = 256 / 8 = 32
```

也就是每个网格大约负责原图上的 `32x32` 区域。对于合成数字、小型自定义物体，这是足够学习的。后续如果要检测小物体，再升级到 `32x32 / 16x16 / 8x8` 多尺度输出。

## 4. 模型总览

第一版网络命名为 `MiniYOLOv1`。

```text
image [B, 3, 256, 256]
-> backbone: 连续下采样，提取视觉特征
-> detection head: 输出 [B, 15, 8, 8]
-> reshape: [B, 8, 8, 15]
-> decode: box + score + class
-> NMS
```

每个输出 cell 的 15 个值含义：

```text
[tx, ty, tw, th, obj_logit, cls0, cls1, ..., cls9]
```

其中：

- `tx, ty`：物体中心点在当前 cell 内的相对偏移。
- `tw, th`：物体宽高，第一版直接预测归一化宽高。
- `obj_logit`：该 cell 是否有物体。
- `cls logits`：类别预测，训练时用 cross entropy。

## 5. 网络层级设计和 shape

约定：

- `B` 是 batch size。
- `ConvBNAct(k=3,s=2,c=32)` 表示 `Conv2d -> BatchNorm2d -> SiLU/ReLU`。
- 所有 `3x3` 卷积使用 `padding=1`。
- 第一版激活函数建议用 `SiLU`，如果想更容易理解，也可以用 `ReLU`。

### 5.1 Backbone + Head shape 表

| 序号 | 模块 | 配置 | 输入 shape | 输出 shape | 作用 |
| --- | --- | --- | --- | --- | --- |
| 0 | Input | RGB image | `[B, 3, 256, 256]` | `[B, 3, 256, 256]` | 输入图片 |
| 1 | StemConv | `ConvBNAct 3x3, s=2, 3->32` | `[B, 3, 256, 256]` | `[B, 32, 128, 128]` | 初步提取边缘/纹理 |
| 2 | ConvBlock | `ConvBNAct 3x3, s=1, 32->32` | `[B, 32, 128, 128]` | `[B, 32, 128, 128]` | 加强低级特征 |
| 3 | Down1 | `ConvBNAct 3x3, s=2, 32->64` | `[B, 32, 128, 128]` | `[B, 64, 64, 64]` | 下采样到 1/4 |
| 4 | ResBlock1 | `ResidualBlock, c=64` | `[B, 64, 64, 64]` | `[B, 64, 64, 64]` | 增加非线性表达 |
| 5 | Down2 | `ConvBNAct 3x3, s=2, 64->128` | `[B, 64, 64, 64]` | `[B, 128, 32, 32]` | 下采样到 1/8 |
| 6 | ResBlock2a | `ResidualBlock, c=128` | `[B, 128, 32, 32]` | `[B, 128, 32, 32]` | 中层形状特征 |
| 7 | ResBlock2b | `ResidualBlock, c=128` | `[B, 128, 32, 32]` | `[B, 128, 32, 32]` | 中层形状特征 |
| 8 | Down3 | `ConvBNAct 3x3, s=2, 128->256` | `[B, 128, 32, 32]` | `[B, 256, 16, 16]` | 下采样到 1/16 |
| 9 | ResBlock3a | `ResidualBlock, c=256` | `[B, 256, 16, 16]` | `[B, 256, 16, 16]` | 高级语义特征 |
| 10 | ResBlock3b | `ResidualBlock, c=256` | `[B, 256, 16, 16]` | `[B, 256, 16, 16]` | 高级语义特征 |
| 11 | Down4 | `ConvBNAct 3x3, s=2, 256->512` | `[B, 256, 16, 16]` | `[B, 512, 8, 8]` | 下采样到 1/32 |
| 12 | ContextConv | `ConvBNAct 3x3, s=1, 512->512` | `[B, 512, 8, 8]` | `[B, 512, 8, 8]` | 扩大语义表达 |
| 13 | HeadConv | `ConvBNAct 3x3, s=1, 512->256` | `[B, 512, 8, 8]` | `[B, 256, 8, 8]` | 检测头前的特征压缩 |
| 14 | PredConv | `Conv2d 1x1, 256->15` | `[B, 256, 8, 8]` | `[B, 15, 8, 8]` | 输出检测预测 |
| 15 | Permute | `NCHW -> NHWC` | `[B, 15, 8, 8]` | `[B, 8, 8, 15]` | 方便 loss 计算 |

### 5.2 ResidualBlock 内部 shape

`ResidualBlock(c)`：

```text
input:  [B, c, H, W]
branch: ConvBNAct 3x3, s=1, c->c
        ConvBNAct 3x3, s=1, c->c
output: input + branch
shape:  [B, c, H, W]
```

例如 `ResidualBlock(128)`：

```text
[B, 128, 32, 32]
-> [B, 128, 32, 32]
-> [B, 128, 32, 32]
```

残差连接的目的不是为了“更像 YOLO”，而是为了让深一点的网络更容易训练，减少梯度传播困难。

## 6. 输出张量拆分

模型输出：

```text
pred_raw: [B, 8, 8, 15]
```

拆成：

```text
pred_xy_raw:  [B, 8, 8, 2]    # tx, ty
pred_wh_raw:  [B, 8, 8, 2]    # tw, th
pred_obj_raw: [B, 8, 8]       # objectness logit
pred_cls_raw: [B, 8, 8, 10]   # class logits
```

第一版解码方式：

```text
pred_xy = sigmoid(pred_xy_raw)
pred_wh = sigmoid(pred_wh_raw)
pred_obj_prob = sigmoid(pred_obj_raw)
pred_cls_prob = softmax(pred_cls_raw)
```

注意：训练 loss 里不要提前对 `obj_logit` 做 sigmoid 再喂给 BCE，应该使用 `BCEWithLogitsLoss`。类别也不要提前 softmax，应该使用 `CrossEntropyLoss`。

## 7. 标注格式

推荐训练数据先使用 YOLO 标注格式：

```text
class_id center_x center_y width height
```

所有坐标都归一化到 `[0, 1]`：

```text
center_x = box_center_x / image_width
center_y = box_center_y / image_height
width    = box_width / image_width
height   = box_height / image_height
```

示例：

```text
7 0.53125 0.40625 0.12500 0.18750
2 0.25000 0.50000 0.10000 0.16000
```

如果当前项目生成的是数字图片，建议每张图旁边生成同名 `.txt`：

```text
images/train/000001.png
labels/train/000001.txt
```

## 8. Target 构建

输入 label 列表：

```text
boxes: [N, 5]
每行: [class_id, cx, cy, w, h]
```

输出 target：

```text
target: [B, 8, 8, 15]
```

每个物体分配给中心点所在的 grid cell：

```text
grid_x = floor(cx * S)
grid_y = floor(cy * S)
```

其中 `S = 8`。

当前 cell 内的相对偏移：

```text
target_tx = cx * S - grid_x
target_ty = cy * S - grid_y
target_tw = w
target_th = h
target_obj = 1
target_class = class_id
```

写入 target：

```text
target[b, grid_y, grid_x, 0] = target_tx
target[b, grid_y, grid_x, 1] = target_ty
target[b, grid_y, grid_x, 2] = target_tw
target[b, grid_y, grid_x, 3] = target_th
target[b, grid_y, grid_x, 4] = 1
target[b, grid_y, grid_x, 5 + class_id] = 1
```

没有物体的 cell：

```text
target[..., 4] = 0
target[..., 5:] = 0
```

第一版限制：

```text
同一个 grid cell 只负责一个物体。
如果两个物体中心落到同一个 cell，第一版可以先保留面积更大的物体，或者跳过后一个物体。
```

这是学习版的简化，后续用 anchor 或多尺度输出解决。

## 9. Loss 设计

### 9.1 正负样本 mask

```text
pos_mask = target[..., 4] == 1    # [B, 8, 8]
neg_mask = target[..., 4] == 0    # [B, 8, 8]
```

只有正样本 cell 参与 box loss 和 class loss。

所有 cell 都参与 objectness loss。

### 9.2 Box loss

第一版使用 Smooth L1，容易实现：

```text
pred_xy = sigmoid(pred_xy_raw)
pred_wh = sigmoid(pred_wh_raw)

box_loss = SmoothL1(
    concat(pred_xy, pred_wh)[pos_mask],
    target[..., 0:4][pos_mask]
)
```

shape：

```text
pred_box_pos:   [N_pos, 4]
target_box_pos: [N_pos, 4]
box_loss: scalar
```

学习稳定后，再把 box loss 升级为 IoU/GIoU/CIoU loss。

### 9.3 Objectness loss

使用 `BCEWithLogitsLoss`：

```text
obj_loss = BCEWithLogitsLoss(
    pred_obj_raw,
    target_obj
)
```

shape：

```text
pred_obj_raw: [B, 8, 8]
target_obj:   [B, 8, 8]
obj_loss: scalar
```

因为负样本 cell 很多，建议第一版加权：

```text
positive weight: 1.0
negative weight: 0.2
```

否则模型可能很快学会“全部预测没有物体”。

### 9.4 Class loss

使用 `CrossEntropyLoss`，只在正样本上计算：

```text
cls_loss = CrossEntropyLoss(
    pred_cls_raw[pos_mask],      # [N_pos, 10]
    target_class_id[pos_mask]    # [N_pos]
)
```

注意这里的 `target_class_id` 是整数类别，不是 one-hot。

### 9.5 总 loss

第一版推荐：

```text
loss = lambda_box * box_loss
     + lambda_obj * obj_loss
     + lambda_cls * cls_loss
```

推荐初始权重：

```text
lambda_box = 5.0
lambda_obj = 1.0
lambda_cls = 1.0
```

训练日志至少打印：

```text
total_loss
box_loss
obj_loss
cls_loss
positive_cell_count
mean_iou_on_positive_cells
```

## 10. 预测解码

模型输出 `[B, 8, 8, 15]` 后，需要把 cell 内预测转成原图归一化 box。

对 cell `(gy, gx)`：

```text
cx = (gx + sigmoid(tx)) / S
cy = (gy + sigmoid(ty)) / S
w  = sigmoid(tw)
h  = sigmoid(th)
```

转换成 `xyxy`：

```text
x1 = cx - w / 2
y1 = cy - h / 2
x2 = cx + w / 2
y2 = cy + h / 2
```

最终分数：

```text
obj_prob = sigmoid(obj_logit)
cls_prob = softmax(cls_logits)
score = obj_prob * max(cls_prob)
class_id = argmax(cls_prob)
```

过滤：

```text
score_threshold = 0.25
```

然后做 NMS：

```text
nms_iou_threshold = 0.45
```

## 11. NMS 要理解什么

NMS 的输入：

```text
boxes:  [N, 4]   # xyxy
scores: [N]
labels: [N]
```

逻辑：

```text
1. 按 score 从大到小排序。
2. 取最高分 box。
3. 删除与它 IoU > threshold 的同类 box。
4. 重复直到没有 box。
```

第一版建议按类别分别 NMS，不同类别之间不要互相删除。

## 12. PyTorch 文件建议

建议后续实现时使用这个目录：

```text
YOLO/
  work/
    mini_yolo_from_scratch_plan.md
  src/
    mini_yolo/
      __init__.py
      model.py          # ConvBNAct, ResidualBlock, MiniYOLOv1
      dataset.py        # YOLO label 读取、图片预处理
      target.py         # build_targets
      loss.py           # detection_loss
      decode.py         # decode_predictions, nms
      train.py          # 训练循环
      evaluate.py       # 验证和可视化
  scripts/
    train_mini_yolo.py
    predict_image.py
  data/
    images/
      train/
      val/
    labels/
      train/
      val/
  runs/
    checkpoints/
    previews/
```

## 13. 实现顺序

### Step 1: 只搭模型并检查 shape

目标：

```text
输入 torch.zeros(2, 3, 256, 256)
输出 shape 必须是 [2, 15, 8, 8]
```

必须写断言：

```text
assert output.shape == (B, 15, 8, 8)
```

### Step 2: 写 label 读取和 target 构建

目标：

```text
一张图片的 YOLO label
-> target [1, 8, 8, 15]
```

必须人工检查一个例子：

```text
cx=0.5, cy=0.5, S=8
grid_x=4, grid_y=4
target_tx=0.0, target_ty=0.0
```

如果这个都不对，后面训练一定失败。

### Step 3: 写 loss 并用假数据测试

先构造一个 target，再构造接近 target 的 pred，确认：

```text
好预测的 loss < 坏预测的 loss
```

这是目标检测里非常关键的 sanity check。

### Step 4: overfit 16 张图片

先不要大规模训练。用 16 张图片训练到明显过拟合：

```text
box_loss 下降
obj_loss 下降
cls_loss 下降
可视化框越来越贴近目标
```

如果 16 张都 overfit 不了，通常是下面之一：

- target 构建错了。
- loss 的 mask 错了。
- 输出 reshape 维度错了。
- box decode 公式错了。
- 学习率太高或太低。

### Step 5: 扩展到 500-5000 张合成数据

推荐第一轮：

```text
train: 1000 images
val:   200 images
epochs: 50
batch_size: 16
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
```

如果 loss 抖动明显，把学习率降到：

```text
3e-4
```

### Step 6: 加验证指标

至少实现：

```text
positive cell class accuracy
mean IoU on positive cells
precision at score threshold 0.25
recall at score threshold 0.25
```

后续再实现标准 mAP。

## 14. 第一版验收标准

完成第一版后，你应该能做到：

- 清楚解释 `[B, 3, 256, 256]` 如何变成 `[B, 15, 8, 8]`。
- 清楚解释每个 cell 的 15 个输出分别是什么。
- 清楚解释一个真实 box 如何分配到某个 grid cell。
- 能写出 `target [B, 8, 8, 15]`。
- 能区分 box loss、objectness loss、class loss。
- 能把模型输出解码成真实坐标框。
- 能用 NMS 去掉重复框。
- 能 overfit 16 张简单图片。
- 能在验证图片上画出预测框。

## 15. 第二版升级方向

第一版跑通后，再逐步升级，不要一次全加。

### 15.1 多尺度检测

增加三个输出头：

```text
P3: [B, 15, 32, 32]   # stride 8, 负责小物体
P4: [B, 15, 16, 16]   # stride 16, 负责中物体
P5: [B, 15, 8, 8]     # stride 32, 负责大物体
```

这时需要一个 neck：

```text
backbone features:
C3: [B, 128, 32, 32]
C4: [B, 256, 16, 16]
C5: [B, 512, 8, 8]

neck:
upsample C5 -> 16x16, concat C4
upsample P4 -> 32x32, concat C3
```

这一步会让模型更像现代 YOLO。

### 15.2 Anchor-based head

把每个 cell 的预测数从 `1` 改为 `A=3`：

```text
output channels = A * (5 + C)
                = 3 * 15
                = 45

output: [B, 45, 8, 8]
reshape: [B, 8, 8, 3, 15]
```

这会引入 anchor 匹配、anchor 尺寸设计、正负样本分配，复杂度明显增加。建议第一版不要做。

### 15.3 IoU/GIoU/CIoU loss

把第一版 Smooth L1 box loss 换成：

```text
iou_loss = 1 - IoU(pred_box, target_box)
```

再进一步学习：

```text
GIoU
DIoU
CIoU
```

这能更贴近真实检测模型。

### 15.4 数据增强

按顺序加入：

```text
random horizontal flip
random scale
random translate
color jitter
mosaic
mixup
```

第一版不建议上来就用 mosaic，因为它会让 target 构建和可视化检查更复杂。

## 16. 学习重点

这条路线的核心不是记住某个 YOLO 版本的代码，而是掌握这些问题：

```text
1. 特征图上的一个位置，如何对应回原图上的一个区域？
2. 模型怎么同时预测类别和位置？
3. 正样本 cell 是怎么选出来的？
4. 为什么 objectness loss 很重要？
5. 为什么负样本太多会影响训练？
6. 为什么需要 NMS？
7. 为什么小物体需要更高分辨率特征图？
8. 为什么检测模型不能只看 accuracy？
```

只要 MiniYOLOv1 能稳定 overfit 小数据，你就已经真正理解了 YOLO 的主链路。后面看官方 YOLO 工程时，复杂点会变成工程细节，而不是黑箱。
