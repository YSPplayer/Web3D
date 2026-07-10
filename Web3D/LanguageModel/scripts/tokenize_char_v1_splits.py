from __future__ import annotations

import json
import sys
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.tokenized_data import tokenize_splits


def main() -> int:
    tokenizer_path = LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1" / "tokenizer.json"
    processed_dir = LANGUAGE_MODEL_ROOT / "data" / "processed"
    output_dir = LANGUAGE_MODEL_ROOT / "data" / "tokenized" / "char_v1"

    try:
        manifest = tokenize_splits(tokenizer_path, processed_dir, output_dir)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
