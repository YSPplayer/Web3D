from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from lm.dataset import TokenDataset
from lm.model import GPTConfig, GPTLanguageModel


def train_step(
    model: GPTLanguageModel,
    optimizer: torch.optim.Optimizer,
    dataset: TokenDataset,
    batch_size: int,
    block_size: int,
    generator: torch.Generator | None = None,
    grad_clip: float | None = 1.0,
) -> float:
    model.train()
    x, y = dataset.get_batch(batch_size=batch_size, block_size=block_size, generator=generator)

    # 每一步训练：清梯度 -> 前向算 loss -> 反向传播 -> 参数更新。
    optimizer.zero_grad(set_to_none=True)
    _, loss = model(x, y)
    if loss is None:
        raise RuntimeError("Training requires targets so loss cannot be None")

    loss.backward()
    if grad_clip is not None:
        # 梯度裁剪可以避免偶发梯度过大，让早期实验更稳定。
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
    optimizer.step()

    return float(loss.detach().cpu().item())


@torch.no_grad()
def estimate_loss(
    model: GPTLanguageModel,
    dataset: TokenDataset,
    batch_size: int,
    block_size: int,
    eval_iters: int,
    generator: torch.Generator | None = None,
) -> float:
    if eval_iters <= 0:
        raise ValueError("eval_iters must be greater than 0")

    previous_training_mode = model.training
    try:
        model.eval()
        losses = []
        for _ in range(eval_iters):
            x, y = dataset.get_batch(batch_size=batch_size, block_size=block_size, generator=generator)
            _, loss = model(x, y)
            if loss is None:
                raise RuntimeError("Evaluation requires targets so loss cannot be None")
            losses.append(loss.detach())

        return float(torch.stack(losses).mean().cpu().item())
    finally:
        # 评估会临时关闭 dropout，结束后恢复调用前的 train/eval 状态。
        model.train(previous_training_mode)


def save_checkpoint(
    checkpoint_dir: str | Path,
    model: GPTLanguageModel,
    optimizer: torch.optim.Optimizer,
    model_config: GPTConfig,
    train_config: dict[str, Any],
    step: int,
    train_loss: float,
    valid_loss: float | None,
    checkpoint_name: str = "model.pt",
) -> Path:
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    if Path(checkpoint_name).name != checkpoint_name:
        raise ValueError("checkpoint_name must be a file name, not a path")

    model_config_dict = asdict(model_config)
    metrics = {
        "train_loss": float(train_loss),
        "valid_loss": None if valid_loss is None else float(valid_loss),
    }

    checkpoint_path = checkpoint_dir / checkpoint_name
    torch.save(
        {
            "step": int(step),
            "model_config": model_config_dict,
            "train_config": train_config,
            "metrics": metrics,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        },
        checkpoint_path,
    )

    # JSON 文件便于直接查看本次实验用了哪些参数，不需要先 torch.load。
    metadata = {
        "step": int(step),
        "model_config": model_config_dict,
        "train_config": train_config,
        "metrics": metrics,
        "checkpoint_name": checkpoint_name,
        "checkpoint": str(checkpoint_path),
    }
    (checkpoint_dir / "training_config.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return checkpoint_path


def save_best_checkpoint_if_improved(
    checkpoint_dir: str | Path,
    model: GPTLanguageModel,
    optimizer: torch.optim.Optimizer,
    model_config: GPTConfig,
    train_config: dict[str, Any],
    step: int,
    train_loss: float,
    valid_loss: float | None,
    best_valid_loss: float | None,
) -> tuple[float | None, bool, Path | None]:
    if valid_loss is None:
        return best_valid_loss, False, None

    # 只用验证集 loss 判断 best；训练集 loss 下降可能只是记住训练集。
    if best_valid_loss is not None and valid_loss >= best_valid_loss:
        return best_valid_loss, False, None

    checkpoint_path = save_checkpoint(
        checkpoint_dir=checkpoint_dir,
        model=model,
        optimizer=optimizer,
        model_config=model_config,
        train_config=train_config,
        step=step,
        train_loss=train_loss,
        valid_loss=valid_loss,
        checkpoint_name="best.pt",
    )
    return float(valid_loss), True, checkpoint_path


def append_metrics_history(history_path: str | Path, record: dict[str, Any]) -> None:
    history_path = Path(history_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # JSONL 一行一条评估记录，训练中断时也能保留已经写入的历史。
    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        file.write("\n")
