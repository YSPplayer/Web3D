from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import torch
import torch.nn.functional as F

from lm.model import GPTConfig, GPTLanguageModel
from lm.tokenizer import CharTokenizer


def resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(requested)


def build_qa_prompt(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")

    # 推理时使用和训练集一致的问答格式，让模型知道接下来应该续写“回答”。
    return f"<|qa_start|>\n问题：{question}\n回答："


def extract_answer(decoded_text: str) -> str:
    answer_marker = "回答："
    answer_start = decoded_text.find(answer_marker)
    if answer_start >= 0:
        answer = decoded_text[answer_start + len(answer_marker) :]
    else:
        answer = decoded_text

    qa_end = answer.find("<|qa_end|>")
    if qa_end >= 0:
        answer = answer[:qa_end]

    return answer.strip()


def load_model_from_checkpoint(
    checkpoint_path: str | Path,
    device: torch.device,
) -> tuple[GPTLanguageModel, GPTConfig, dict[str, Any]]:
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint does not exist: {checkpoint_path}")

    payload = torch.load(checkpoint_path, map_location=device)
    if "model_config" not in payload:
        raise KeyError("Checkpoint missing model_config")
    if "model_state_dict" not in payload:
        raise KeyError("Checkpoint missing model_state_dict")

    model_config = GPTConfig(**payload["model_config"])
    model = GPTLanguageModel(model_config).to(device)
    model.load_state_dict(payload["model_state_dict"])
    model.eval()
    return model, model_config, payload


@torch.no_grad()
def generate_token_ids(
    model: GPTLanguageModel,
    input_ids: Iterable[int],
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    stop_ids: set[int] | None,
    device: torch.device,
    generator: torch.Generator | None = None,
) -> list[int]:
    ids = [int(token_id) for token_id in input_ids]
    if not ids:
        raise ValueError("input_ids must not be empty")
    if max_new_tokens < 0:
        raise ValueError("max_new_tokens must be greater than or equal to 0")
    if temperature < 0:
        raise ValueError("temperature must be greater than or equal to 0")
    if top_k is not None and top_k <= 0:
        raise ValueError("top_k must be greater than 0 when provided")

    model.eval()
    idx = torch.tensor([ids], dtype=torch.long, device=device)
    stop_ids = stop_ids or set()

    for _ in range(max_new_tokens):
        # Transformer 的上下文长度有限；超出 block_size 时只把最近窗口送入模型。
        idx_cond = idx[:, -model.config.block_size :]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :]

        if temperature == 0:
            next_idx = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            logits = logits / temperature
            if top_k is not None:
                k = min(top_k, logits.shape[-1])
                values, _ = torch.topk(logits, k=k, dim=-1)
                threshold = values[:, -1].unsqueeze(-1)
                logits = torch.where(logits < threshold, torch.full_like(logits, float("-inf")), logits)

            probs = F.softmax(logits, dim=-1)
            next_idx = torch.multinomial(probs, num_samples=1, generator=generator)

        idx = torch.cat((idx, next_idx), dim=1)
        if int(next_idx.item()) in stop_ids:
            break

    return idx[0].detach().cpu().tolist()


def generate_answer(
    model: GPTLanguageModel,
    tokenizer: CharTokenizer,
    question: str,
    device: torch.device,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_k: int | None = 50,
) -> tuple[str, str]:
    prompt = build_qa_prompt(question)
    input_ids = tokenizer.encode(prompt)
    qa_end_id = tokenizer.special_tokens.get("<|qa_end|>")
    stop_ids = set() if qa_end_id is None else {qa_end_id}

    generated_ids = generate_token_ids(
        model=model,
        input_ids=input_ids,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        stop_ids=stop_ids,
        device=device,
    )
    decoded_text = tokenizer.decode(generated_ids)
    return extract_answer(decoded_text), decoded_text
