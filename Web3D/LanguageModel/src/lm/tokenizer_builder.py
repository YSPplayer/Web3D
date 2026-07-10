from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SPECIAL_TOKENS = [
    "<pad>",
    "<unk>",
    "<bos>",
    "<eos>",
    "<|file_start|>",
    "<|file_content|>",
    "<|file_end|>",
    "<|qa_start|>",
    "<|qa_end|>",
]


def build_char_tokenizer_data(
    corpus_text: str,
    source_corpus: str = "data/processed/corpus.txt",
    source_corpus_bytes: int | None = None,
) -> dict[str, object]:
    special_tokens = {token: index for index, token in enumerate(SPECIAL_TOKENS)}

    # 普通字符必须排除特殊 token 中的字符组合；特殊标记由 tokenizer 的 special-aware 逻辑整段匹配。
    normal_chars = sorted(set(corpus_text))
    token_to_id = dict(special_tokens)
    for char in normal_chars:
        if char in token_to_id:
            continue
        token_to_id[char] = len(token_to_id)

    id_to_token = {str(token_id): token for token, token_id in token_to_id.items()}

    return {
        "schema_version": 1,
        "name": "char_v1",
        "tokenizer_type": "character_with_structural_special_tokens",
        "description": (
            "Character-level tokenizer vocabulary built from data/processed/corpus.txt. "
            "Structural markers are reserved as special tokens for special-aware encoding; "
            "all other entries are single Unicode characters."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "source_corpus": source_corpus,
        "source_corpus_bytes": len(corpus_text.encode("utf-8")) if source_corpus_bytes is None else source_corpus_bytes,
        "special_tokens": special_tokens,
        "vocab_size": len(token_to_id),
        "normal_char_count": len(token_to_id) - len(special_tokens),
        "normal_chars_sorted_by_unicode": normal_chars,
        "token_to_id": token_to_id,
        "id_to_token": id_to_token,
    }


def build_summary(tokenizer_data: dict[str, object], output_path: Path) -> dict[str, object]:
    normal_chars = tokenizer_data["normal_chars_sorted_by_unicode"]
    if not isinstance(normal_chars, list):
        normal_chars = []

    return {
        "name": tokenizer_data["name"],
        "vocab_size": tokenizer_data["vocab_size"],
        "special_token_count": len(SPECIAL_TOKENS),
        "normal_char_count": tokenizer_data["normal_char_count"],
        "source_corpus_bytes": tokenizer_data["source_corpus_bytes"],
        "output": str(output_path),
        "first_20_normal_chars": normal_chars[:20],
    }


def write_char_tokenizer(
    corpus_text: str,
    output_dir: str | Path,
    source_corpus: str = "data/processed/corpus.txt",
    source_corpus_bytes: int | None = None,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer_path = output_dir / "tokenizer.json"
    summary_path = output_dir / "summary.json"
    tokenizer_data = build_char_tokenizer_data(
        corpus_text=corpus_text,
        source_corpus=source_corpus,
        source_corpus_bytes=source_corpus_bytes,
    )
    summary = build_summary(tokenizer_data, tokenizer_path)

    tokenizer_path.write_text(json.dumps(tokenizer_data, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return tokenizer_path, summary_path
