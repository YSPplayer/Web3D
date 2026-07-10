from __future__ import annotations

import json
import sys
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.tokenizer_builder import write_char_tokenizer


def main() -> int:
    corpus_path = LANGUAGE_MODEL_ROOT / "data" / "processed" / "corpus.txt"
    output_dir = LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1"

    corpus_text = corpus_path.read_text(encoding="utf-8")
    tokenizer_path, summary_path = write_char_tokenizer(
        corpus_text=corpus_text,
        output_dir=output_dir,
        source_corpus=str(corpus_path),
        source_corpus_bytes=corpus_path.stat().st_size,
    )

    print(json.dumps({"tokenizer": str(tokenizer_path), "summary": str(summary_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
