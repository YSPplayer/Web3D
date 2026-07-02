from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lm.tokenizer import CharTokenizer


def encode_text_file(path: str | Path, tokenizer: CharTokenizer) -> list[int]:
    text_path = Path(path)
    text = text_path.read_text(encoding="utf-8")
    return tokenizer.encode(text)


def save_token_ids_pt(ids: Iterable[int], output_path: str | Path) -> None:
    try:
        import torch
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "PyTorch is required to write .pt token id files. "
            "Install torch in the Python environment before running tokenization."
        ) from error

    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tensor = torch.tensor(list(ids), dtype=torch.long)
    torch.save(tensor, target_path)


def tokenize_split(
    split_name: str,
    source_path: str | Path,
    output_path: str | Path,
    tokenizer: CharTokenizer,
) -> dict[str, object]:
    ids = encode_text_file(source_path, tokenizer)
    save_token_ids_pt(ids, output_path)

    return {
        "split": split_name,
        "source": str(source_path),
        "output": str(output_path),
        "num_tokens": len(ids),
    }


def tokenize_splits(
    tokenizer_path: str | Path,
    processed_dir: str | Path,
    output_dir: str | Path,
    splits: tuple[str, ...] = ("train", "valid", "test"),
) -> dict[str, object]:
    tokenizer = CharTokenizer.from_file(tokenizer_path)
    processed_path = Path(processed_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    split_entries = {}
    for split in splits:
        source = processed_path / f"{split}.txt"
        target = output_path / f"{split}_ids.pt"
        split_entries[split] = tokenize_split(split, source, target, tokenizer)

    manifest = {
        "schema_version": 1,
        "tokenizer_name": tokenizer.name,
        "tokenizer_path": str(tokenizer_path),
        "vocab_size": tokenizer.vocab_size,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "splits": split_entries,
    }
    (output_path / "tokenized_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest

