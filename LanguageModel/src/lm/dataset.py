from __future__ import annotations

from pathlib import Path

import torch


class TokenDataset:
    def __init__(self, ids_path: str | Path, device: str | torch.device = "cpu") -> None:
        self.ids_path = Path(ids_path)
        self.device = torch.device(device)

        tokens = torch.load(self.ids_path, map_location="cpu")
        if not isinstance(tokens, torch.Tensor):
            raise TypeError(f"Token id file must contain a torch.Tensor: {self.ids_path}")
        if tokens.dim() != 1:
            raise ValueError(f"Token id tensor must be one-dimensional, got shape {tuple(tokens.shape)}")
        if tokens.dtype != torch.long:
            raise TypeError(f"Token id tensor must use torch.long dtype, got {tokens.dtype}")

        # 训练数据先保存在 CPU 上；每次 get_batch 时再把小批量移动到目标设备。
        # 这样可以避免一次性把完整训练集搬到显存里。
        self.tokens = tokens.contiguous()

    @property
    def num_tokens(self) -> int:
        return int(self.tokens.numel())

    def get_batch(
        self,
        batch_size: int,
        block_size: int,
        generator: torch.Generator | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        if block_size <= 0:
            raise ValueError("block_size must be greater than 0")
        if self.num_tokens <= block_size:
            raise ValueError(
                "Token sequence length must be greater than block_size, "
                f"got num_tokens={self.num_tokens}, block_size={block_size}"
            )

        # 随机选择每个样本的起点 i。
        # y 需要访问 i + block_size 这个位置，所以最大起点是 num_tokens - block_size - 1。
        starts = torch.randint(
            low=0,
            high=self.num_tokens - block_size,
            size=(batch_size,),
            generator=generator,
        )

        # x 是当前窗口，y 是同一窗口右移一个 token 后的训练目标。
        # 对 causal LM 来说，模型输入 x，目标是预测 y 中的下一个 token。
        x = torch.stack([self.tokens[start : start + block_size] for start in starts])
        y = torch.stack([self.tokens[start + 1 : start + block_size + 1] for start in starts])

        return x.to(self.device), y.to(self.device)
