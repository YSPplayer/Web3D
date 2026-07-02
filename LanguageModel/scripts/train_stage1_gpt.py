#训练命令:
#$env:PYTHONIOENCODING='utf-8'
#D:\YueShaoPu\lutis\.venv\Scripts\python.exe D:\YueShaoPu\Web3D\LanguageModel\scripts\train_stage1_gpt.py --max-iters 0 --checkpoint-dir D:\YueShaoPu\Web3D\LanguageModel\checkpoints\stage1_char_gpt_v2_qa
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.dataset import TokenDataset
from lm.model import GPTConfig, GPTLanguageModel
from lm.tokenizer import CharTokenizer
from lm.training import (
    append_metrics_history,
    estimate_loss,
    load_training_checkpoint,
    read_best_valid_loss,
    resolve_resume_checkpoint,
    restore_training_state,
    save_best_checkpoint_if_improved,
    save_checkpoint,
    should_stop_for_escape_key,
    train_step,
    update_early_stopping,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the stage1 character-level GPT model.")

    parser.add_argument(
        "--tokenizer",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1" / "tokenizer.json",
    )
    parser.add_argument(
        "--train-ids",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "data" / "tokenized" / "char_v1" / "train_ids.pt",
    )
    parser.add_argument(
        "--valid-ids",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "data" / "tokenized" / "char_v1" / "valid_ids.pt",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=LANGUAGE_MODEL_ROOT / "checkpoints" / "stage1_char_gpt_v1",
    )

    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-iters", type=int, default=1000, help="Use 0 to train until stopped.")
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--log-interval", type=int, default=10)
    parser.add_argument(
        "--early-stop-patience",
        type=int,
        default=0,
        help="Stop after this many evaluations without a new best valid_loss. Default 0 disables automatic early stopping.",
    )
    parser.add_argument(
        "--disable-esc-stop",
        action="store_true",
        help="Disable Windows ESC key polling; Ctrl+C still saves latest.pt.",
    )

    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Resume training from a checkpoint, usually checkpoints/.../latest.pt.",
    )
    parser.add_argument(
        "--auto-resume",
        action="store_true",
        help="If checkpoint-dir/latest.pt exists, resume from it. Otherwise start from scratch.",
    )

    return parser.parse_args()


def resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(requested)


def main() -> int:
    args = parse_args()
    device = resolve_device(args.device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    resume_path = resolve_resume_checkpoint(
        checkpoint_dir=args.checkpoint_dir,
        resume_path=args.resume,
        auto_resume=args.auto_resume,
    )
    resume_payload = None

    tokenizer = CharTokenizer.from_file(args.tokenizer)
    if resume_path is not None:
        model_config, resume_payload = load_training_checkpoint(resume_path, device=device)
        if model_config.vocab_size != tokenizer.vocab_size:
            raise ValueError(
                "Checkpoint vocab_size does not match tokenizer vocab_size, "
                f"checkpoint={model_config.vocab_size}, tokenizer={tokenizer.vocab_size}"
            )
    else:
        model_config = GPTConfig(
            vocab_size=tokenizer.vocab_size,
            block_size=args.block_size,
            n_embd=args.n_embd,
            n_head=args.n_head,
            n_layer=args.n_layer,
            dropout=args.dropout,
        )
    train_config = {
        "tokenizer": str(args.tokenizer),
        "train_ids": str(args.train_ids),
        "valid_ids": str(args.valid_ids),
        "checkpoint_dir": str(args.checkpoint_dir),
        "resume": None if args.resume is None else str(args.resume),
        "auto_resume": args.auto_resume,
        "resolved_resume": None if resume_path is None else str(resume_path),
        "device": str(device),
        "seed": args.seed,
        "max_iters": args.max_iters,
        "eval_interval": args.eval_interval,
        "eval_iters": args.eval_iters,
        "log_interval": args.log_interval,
        "early_stop_patience": args.early_stop_patience,
        "disable_esc_stop": args.disable_esc_stop,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "grad_clip": args.grad_clip,
    }

    print("[config]")
    print(json.dumps({"model": model_config.__dict__, "train": train_config}, ensure_ascii=False, indent=2))

    train_dataset = TokenDataset(args.train_ids, device=device)
    valid_dataset = TokenDataset(args.valid_ids, device=device)
    model = GPTLanguageModel(model_config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    start_step = 0
    if resume_payload is not None:
        start_step = restore_training_state(model, optimizer, resume_payload)

    param_count = sum(parameter.numel() for parameter in model.parameters())
    print(f"[start] device={device}, params={param_count}, train_tokens={train_dataset.num_tokens}")
    if resume_path is not None:
        print(f"[resume] checkpoint={resume_path}, start_step={start_step}")

    generator = torch.Generator().manual_seed(args.seed)
    resume_metrics = {} if resume_payload is None else resume_payload.get("metrics", {})
    last_train_loss = float(resume_metrics.get("train_loss", float("nan")))
    last_valid_loss: float | None = resume_metrics.get("valid_loss")
    if last_valid_loss is not None:
        last_valid_loss = float(last_valid_loss)
    best_valid_loss: float | None = None
    if resume_payload is not None:
        best_valid_loss = read_best_valid_loss(args.checkpoint_dir, device=device)
    if best_valid_loss is None:
        best_valid_loss = last_valid_loss
    latest_checkpoint_path: Path | None = None
    existing_best_path = args.checkpoint_dir / "best.pt"
    best_checkpoint_path: Path | None = existing_best_path if resume_payload is not None and existing_best_path.exists() else None
    metrics_history_path = args.checkpoint_dir / "metrics_history.jsonl"
    stale_evals = 0
    completed_step = start_step
    stop_reason: str | None = None
    started_at = time.time()

    try:
        step = start_step
        while args.max_iters == 0 or step < args.max_iters:
            step += 1
            step_started_at = time.time()
            last_train_loss = train_step(
                model=model,
                optimizer=optimizer,
                dataset=train_dataset,
                batch_size=args.batch_size,
                block_size=args.block_size,
                generator=generator,
                grad_clip=args.grad_clip,
            )
            completed_step = step

            should_log = step == 1 or step % args.log_interval == 0
            should_eval = step == 1 or step % args.eval_interval == 0 or step == args.max_iters

            if should_eval:
                last_valid_loss = estimate_loss(
                    model=model,
                    dataset=valid_dataset,
                    batch_size=args.batch_size,
                    block_size=args.block_size,
                    eval_iters=args.eval_iters,
                    generator=generator,
                )
                latest_checkpoint_path = save_checkpoint(
                    checkpoint_dir=args.checkpoint_dir,
                    model=model,
                    optimizer=optimizer,
                    model_config=model_config,
                    train_config=train_config,
                    step=step,
                    train_loss=last_train_loss,
                    valid_loss=last_valid_loss,
                    checkpoint_name="latest.pt",
                )
                best_valid_loss, improved, saved_best_path = save_best_checkpoint_if_improved(
                    checkpoint_dir=args.checkpoint_dir,
                    model=model,
                    optimizer=optimizer,
                    model_config=model_config,
                    train_config=train_config,
                    step=step,
                    train_loss=last_train_loss,
                    valid_loss=last_valid_loss,
                    best_valid_loss=best_valid_loss,
                )
                if saved_best_path is not None:
                    best_checkpoint_path = saved_best_path

                early_stop = update_early_stopping(
                    improved=improved,
                    stale_evals=stale_evals,
                    patience=args.early_stop_patience,
                )
                stale_evals = early_stop.stale_evals
                if early_stop.should_stop:
                    stop_reason = early_stop.reason

                append_metrics_history(
                    metrics_history_path,
                    {
                        "step": step,
                        "train_loss": last_train_loss,
                        "valid_loss": last_valid_loss,
                        "best_valid_loss": best_valid_loss,
                        "stale_evals": stale_evals,
                        "is_best": improved,
                        "stop_reason": stop_reason,
                        "latest_checkpoint": str(latest_checkpoint_path),
                        "best_checkpoint": None if best_checkpoint_path is None else str(best_checkpoint_path),
                    },
                )

            if should_log or should_eval:
                elapsed_ms = (time.time() - step_started_at) * 1000
                valid_part = "" if last_valid_loss is None else f", valid_loss={last_valid_loss:.4f}"
                best_part = "" if best_valid_loss is None else f", best_valid_loss={best_valid_loss:.4f}"
                stale_part = f", stale_evals={stale_evals}" if args.early_stop_patience > 0 else ""
                print(
                    f"[step {step:05d}] train_loss={last_train_loss:.4f}"
                    f"{valid_part}{best_part}{stale_part}, {elapsed_ms:.1f} ms"
                )

            if stop_reason is not None:
                print(f"[stop] {stop_reason}")
                break

            if not args.disable_esc_stop and should_stop_for_escape_key():
                stop_reason = "ESC pressed"
                print("[stop] ESC pressed")
                break
    except KeyboardInterrupt:
        stop_reason = "Ctrl+C pressed"
        print("\n[stop] Ctrl+C pressed")

    if completed_step > 0 or stop_reason is not None:
        latest_checkpoint_path = save_checkpoint(
            checkpoint_dir=args.checkpoint_dir,
            model=model,
            optimizer=optimizer,
            model_config=model_config,
            train_config=train_config,
            step=completed_step,
            train_loss=last_train_loss,
            valid_loss=last_valid_loss,
            checkpoint_name="latest.pt",
        )
        if stop_reason is not None:
            append_metrics_history(
                metrics_history_path,
                {
                    "event": "stop",
                    "step": completed_step,
                    "train_loss": last_train_loss,
                    "valid_loss": last_valid_loss,
                    "best_valid_loss": best_valid_loss,
                    "stale_evals": stale_evals,
                    "stop_reason": stop_reason,
                    "latest_checkpoint": str(latest_checkpoint_path),
                    "best_checkpoint": None if best_checkpoint_path is None else str(best_checkpoint_path),
                },
            )

    elapsed_sec = time.time() - started_at
    print(f"[done] elapsed={elapsed_sec:.1f}s")
    print(f"[done] stop_reason={stop_reason}")
    print(f"[done] latest_checkpoint={latest_checkpoint_path}")
    print(f"[done] best_checkpoint={best_checkpoint_path}")
    print(f"[done] metrics_history={metrics_history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
