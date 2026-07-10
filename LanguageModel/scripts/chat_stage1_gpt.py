from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.inference import generate_answer, load_model_from_checkpoint, resolve_device
from lm.tokenizer import CharTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local console chat with the stage1 GPT model.")
    parser.add_argument(
        "--tokenizer",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1" / "tokenizer.json",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "checkpoints" / "stage1_char_gpt_v1" / "best.pt",
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--prompt", type=str, default=None, help="Ask one question and exit.")
    parser.add_argument("--show-raw", action="store_true", help="Print the full decoded model text.")
    return parser.parse_args()


def print_answer(
    model,
    tokenizer: CharTokenizer,
    question: str,
    device: torch.device,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    show_raw: bool,
) -> None:
    answer, raw_text = generate_answer(
        model=model,
        tokenizer=tokenizer,
        question=question,
        device=device,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
    )
    print(f"模型：{answer}")
    if show_raw:
        print("[raw]")
        print(raw_text)


def main() -> int:
    args = parse_args()
    device = resolve_device(args.device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    top_k = None if args.top_k <= 0 else args.top_k
    tokenizer = CharTokenizer.from_file(args.tokenizer)
    model, model_config, payload = load_model_from_checkpoint(args.checkpoint, device=device)
    step = payload.get("step", "unknown")

    print(f"[loaded] checkpoint={args.checkpoint}")
    print(f"[loaded] device={device}, step={step}, block_size={model_config.block_size}")

    if args.prompt is not None:
        print_answer(
            model=model,
            tokenizer=tokenizer,
            question=args.prompt,
            device=device,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=top_k,
            show_raw=args.show_raw,
        )
        return 0

    print("Stage1 Char GPT console. Type /exit to quit.")
    while True:
        try:
            question = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question in {"/exit", "/quit", "/q"}:
            break

        try:
            print_answer(
                model=model,
                tokenizer=tokenizer,
                question=question,
                device=device,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                top_k=top_k,
                show_raw=args.show_raw,
            )
        except ValueError as error:
            print(f"[error] {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
