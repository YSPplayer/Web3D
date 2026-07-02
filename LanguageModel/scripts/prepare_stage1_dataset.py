from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
WEB3D_ROOT = Path(r"D:\YueShaoPu\Web3D")
PROJECTYJT_ROOT = Path(r"D:\work\projectyjt")

RAW_DIR = LANGUAGE_MODEL_ROOT / "data" / "raw"
PROCESSED_DIR = LANGUAGE_MODEL_ROOT / "data" / "processed"
SYNTHETIC_QA_SOURCE_DIR = RAW_DIR / "synthetic_qa"
SYNTHETIC_QA_SOURCE_PATH = SYNTHETIC_QA_SOURCE_DIR / "synthetic_zh_qa_seed.json"
SYNTHETIC_QA_PATH = RAW_DIR / "synthetic_zh_qa.txt"

MAX_FILE_BYTES = 80 * 1024
MAX_SOURCE_BLOCKS = 80
RANDOM_SEED = 20260701

ALLOWED_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".ts",
    ".vue",
    ".java",
    ".yml",
    ".yaml",
    ".json",
}

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".codex-temp",
    ".playwright-mcp",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    ".cache",
    "__pycache__",
    "native/Package".lower(),
    "LanguageModel/data".lower(),
}

EXCLUDED_FILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "upload.json",
    "tmp-frontend-dev.log",
}


@dataclass(frozen=True)
class SourceFile:
    root_label: str
    root: Path
    path: Path
    rel: str
    priority: int


@dataclass(frozen=True)
class TextBlock:
    block_id: str
    source: str
    kind: str
    language: str
    text: str

    @property
    def chars(self) -> int:
        return len(self.text)


def path_has_excluded_dir(rel: Path) -> bool:
    parts = [p.lower() for p in rel.parts]
    joined = "/".join(parts)
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    return any(excluded in joined for excluded in EXCLUDED_DIRS if "/" in excluded)


def is_under(rel: Path, *prefix_parts: str) -> bool:
    parts = tuple(p.lower() for p in rel.parts)
    prefix = tuple(p.lower() for p in prefix_parts)
    return parts[: len(prefix)] == prefix


def should_include_web3d(rel: Path) -> bool:
    name = rel.name
    if name in {"README.md", "LEARN.md", "package.json", "tsconfig.json", "vite.config.ts"}:
        return True
    return (
        is_under(rel, "native", "Work")
        or is_under(rel, "native", "src", "Neural")
        or is_under(rel, "native", "src", "Web")
        or is_under(rel, "backend", "src")
        or is_under(rel, "src")
        or is_under(rel, "tools")
    )


def should_include_projectyjt(rel: Path) -> bool:
    name = rel.name
    if name in {"README.md", "AGENTS.md"}:
        return True
    return (
        is_under(rel, "Work")
        or is_under(rel, "docs")
        or is_under(rel, "apps", "frontend", "src")
        or is_under(rel, "services")
        or is_under(rel, "engines")
        or is_under(rel, "tools")
        or is_under(rel, "inference", "triton")
        or is_under(rel, "infra", "docker-compose")
    )


def source_priority(root_label: str, rel: Path) -> int:
    ext = rel.suffix.lower()
    if root_label == "web3d":
        base = 0
    else:
        base = 100

    if ext == ".md":
        return base + 0
    if is_under(rel, "native", "src", "Neural") or is_under(rel, "engines"):
        return base + 10
    if ext in {".cpp", ".c", ".h", ".hpp"}:
        return base + 20
    if ext in {".py", ".java", ".ts", ".vue"}:
        return base + 30
    return base + 50


def collect_source_files() -> tuple[list[SourceFile], list[dict[str, object]]]:
    roots = [
        ("web3d", WEB3D_ROOT, should_include_web3d),
        ("projectyjt", PROJECTYJT_ROOT, should_include_projectyjt),
    ]
    candidates: list[SourceFile] = []
    skipped: list[dict[str, object]] = []

    for root_label, root, include_func in roots:
        if not root.exists():
            skipped.append({"path": str(root), "reason": "root_not_found"})
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            try:
                rel_path = path.relative_to(root)
            except ValueError:
                continue

            if path_has_excluded_dir(rel_path):
                continue
            if path.name in EXCLUDED_FILE_NAMES:
                continue
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            if not include_func(rel_path):
                continue

            size = path.stat().st_size
            if size == 0:
                skipped.append({"path": str(path), "reason": "empty_file"})
                continue
            if size > MAX_FILE_BYTES:
                skipped.append({"path": str(path), "reason": "too_large", "bytes": size})
                continue

            rel = f"{root_label}/{rel_path.as_posix()}"
            candidates.append(
                SourceFile(
                    root_label=root_label,
                    root=root,
                    path=path,
                    rel=rel,
                    priority=source_priority(root_label, rel_path),
                )
            )

    candidates.sort(key=lambda item: (item.priority, item.rel.lower()))
    return candidates[:MAX_SOURCE_BLOCKS], skipped


def read_text(path: Path) -> str | None:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "cp936"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return None


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def looks_binary_or_bad(text: str) -> bool:
    if not text:
        return True
    control_count = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\t")
    return control_count / max(len(text), 1) > 0.01


def language_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".md": "markdown",
        ".txt": "text",
        ".py": "python",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "cpp-header",
        ".hpp": "cpp-header",
        ".ts": "typescript",
        ".vue": "vue",
        ".java": "java",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
    }.get(ext, "text")


def make_source_block(source: SourceFile, content: str) -> TextBlock:
    language = language_for_path(source.path)
    block = (
        "<|file_start|>\n"
        f"source: {source.rel}\n"
        f"language: {language}\n"
        "kind: source_or_document\n"
        "<|file_content|>\n"
        f"{content}\n"
        "<|file_end|>\n"
    )
    return TextBlock(
        block_id=source.rel,
        source=source.rel,
        kind="source_or_document",
        language=language,
        text=block,
    )

def synthetic_qa_source_paths(path: Path | None = None) -> list[Path]:
    if path is None:
        return sorted(SYNTHETIC_QA_SOURCE_DIR.glob("*.json"))
    if path.is_dir():
        return sorted(path.glob("*.json"))
    return [path]


def load_synthetic_qa_items(path: Path | None = None) -> list[dict[str, object]]:
    source_paths = synthetic_qa_source_paths(path)
    if not source_paths:
        raise FileNotFoundError(f"No synthetic QA JSON files found: {SYNTHETIC_QA_SOURCE_DIR}")

    items: list[dict[str, object]] = []
    seen_sources: set[str] = set()
    for source_path in source_paths:
        raw_items = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raise ValueError(f"Synthetic QA JSON must be a list: {source_path}")

        for index, raw_item in enumerate(raw_items, start=1):
            if not isinstance(raw_item, dict):
                raise ValueError(f"Synthetic QA item #{index} must be an object: {source_path}")

            question = str(raw_item.get("question", "")).strip()
            answer = str(raw_item.get("answer", "")).strip()
            if not question or not answer:
                raise ValueError(f"Synthetic QA item #{index} must include question and answer: {source_path}")

            source = str(raw_item.get("source") or f"{source_path.stem}/{index:03d}").strip()
            if source in seen_sources:
                raise ValueError(f"Duplicate synthetic QA source: {source}")
            seen_sources.add(source)

            language = str(raw_item.get("language") or "zh+en").strip()
            kind = str(raw_item.get("kind") or "synthetic_learning_qa").strip()
            tags = raw_item.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            items.append(
                {
                    "source": source,
                    "language": language,
                    "kind": kind,
                    "question": question,
                    "answer": answer,
                    "tags": tags,
                    "source_file": str(source_path),
                }
            )
    return items


def make_qa_blocks() -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for item in load_synthetic_qa_items():
        source = str(item["source"])
        language = str(item["language"])
        kind = str(item["kind"])
        question = str(item["question"])
        answer = str(item["answer"])
        text = (
            "<|qa_start|>\n"
            f"source: {source}\n"
            f"language: {language}\n"
            f"kind: {kind}\n"
            f"\u95ee\u9898\uff1a{question}\n"
            f"\u56de\u7b54\uff1a{answer}\n"
            "<|qa_end|>\n"
        )
        blocks.append(
            TextBlock(
                block_id=source,
                source=source,
                kind=kind,
                language=language,
                text=text,
            )
        )
    return blocks


def build_source_blocks(source_files: list[SourceFile]) -> tuple[list[TextBlock], list[dict[str, object]]]:
    blocks: list[TextBlock] = []
    skipped: list[dict[str, object]] = []

    for source in source_files:
        raw = read_text(source.path)
        if raw is None:
            skipped.append({"path": str(source.path), "reason": "decode_failed"})
            continue

        normalized = normalize_text(raw)
        if looks_binary_or_bad(normalized):
            skipped.append({"path": str(source.path), "reason": "binary_or_bad_text"})
            continue

        blocks.append(make_source_block(source, normalized))

    return blocks, skipped


def write_blocks(path: Path, blocks: list[TextBlock]) -> None:
    path.write_text("\n".join(block.text for block in blocks) + "\n", encoding="utf-8")


def split_by_char(blocks: list[TextBlock], seed: int) -> dict[str, list[TextBlock]]:
    shuffled = list(blocks)
    random.Random(seed).shuffle(shuffled)
    total_chars = sum(block.chars for block in shuffled)
    target_test = max(int(total_chars * 0.05), 1)
    target_valid = max(int(total_chars * 0.05), 1)

    splits = {"train": [], "valid": [], "test": []}
    test_chars = 0
    valid_chars = 0

    for block in shuffled:
        if test_chars < target_test:
            splits["test"].append(block)
            test_chars += block.chars
        elif valid_chars < target_valid:
            splits["valid"].append(block)
            valid_chars += block.chars
        else:
            splits["train"].append(block)

    return splits


def split_by_count(blocks: list[TextBlock], seed: int, valid_ratio: float, test_ratio: float) -> dict[str, list[TextBlock]]:
    shuffled = list(blocks)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    test_count = max(int(round(total * test_ratio)), 1) if total else 0
    valid_count = max(int(round(total * valid_ratio)), 1) if total else 0

    test = shuffled[:test_count]
    valid = shuffled[test_count : test_count + valid_count]
    train = shuffled[test_count + valid_count :]
    return {"train": train, "valid": valid, "test": test}


def split_blocks(blocks: list[TextBlock]) -> dict[str, list[TextBlock]]:
    source_blocks = [block for block in blocks if block.kind != "synthetic_learning_qa"]
    qa_blocks = [block for block in blocks if block.kind == "synthetic_learning_qa"]

    source_splits = split_by_char(source_blocks, RANDOM_SEED)
    qa_splits = split_by_count(
        qa_blocks,
        seed=RANDOM_SEED + 1,
        valid_ratio=0.10,
        test_ratio=0.10,
    )

    merged = {
        name: source_splits[name] + qa_splits[name]
        for name in ("train", "valid", "test")
    }
    for index, name in enumerate(("train", "valid", "test")):
        random.Random(RANDOM_SEED + 10 + index).shuffle(merged[name])
    return merged


def split_stats(blocks: list[TextBlock]) -> dict[str, object]:
    return {
        "blocks": len(blocks),
        "chars": sum(block.chars for block in blocks),
        "kib": round(sum(block.chars for block in blocks) / 1024, 2),
        "kinds": dict(Counter(block.kind for block in blocks)),
        "languages": dict(Counter(block.language for block in blocks)),
    }


def write_manifest(
    source_files: list[SourceFile],
    source_blocks: list[TextBlock],
    qa_blocks: list[TextBlock],
    splits: dict[str, list[TextBlock]],
    skipped: list[dict[str, object]],
) -> None:
    manifest = {
        "dataset_name": "stage1_from_scratch_language_model",
        "purpose": "Small causal language model learning corpus: Chinese explanations plus English/programming code.",
        "random_seed": RANDOM_SEED,
        "max_file_bytes": MAX_FILE_BYTES,
        "max_source_blocks": MAX_SOURCE_BLOCKS,
        "roots": {
            "web3d": str(WEB3D_ROOT),
            "projectyjt": str(PROJECTYJT_ROOT),
            "language_model": str(LANGUAGE_MODEL_ROOT),
        },
        "outputs": {
            "raw_synthetic_qa_sources": [str(path) for path in synthetic_qa_source_paths()],
            "raw_synthetic_qa": str(SYNTHETIC_QA_PATH),
            "corpus": str(PROCESSED_DIR / "corpus.txt"),
            "train": str(PROCESSED_DIR / "train.txt"),
            "valid": str(PROCESSED_DIR / "valid.txt"),
            "test": str(PROCESSED_DIR / "test.txt"),
        },
        "source_candidates_used": len(source_files),
        "source_blocks_written": len(source_blocks),
        "synthetic_qa_blocks_written": len(qa_blocks),
        "total": split_stats(source_blocks + qa_blocks),
        "splits": {name: split_stats(items) for name, items in splits.items()},
        "source_extension_counts": dict(Counter(item.path.suffix.lower() for item in source_files)),
        "source_root_counts": dict(Counter(item.root_label for item in source_files)),
        "skipped_count": len(skipped),
        "skipped_samples": skipped[:80],
        "notes": [
            "Files are split by whole text blocks instead of random characters.",
            "The dataset is plain UTF-8 text for causal language model pretraining.",
            "Synthetic QA blocks are learning-oriented Chinese explanations with English programming terms.",
            "Generated dependency/build/vendor/binary files are excluded.",
        ],
    }
    (PROCESSED_DIR / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    source_files, skipped_collect = collect_source_files()
    source_blocks, skipped_read = build_source_blocks(source_files)
    qa_blocks = make_qa_blocks()

    SYNTHETIC_QA_PATH.write_text("\n".join(block.text for block in qa_blocks) + "\n", encoding="utf-8")

    all_blocks = source_blocks + qa_blocks
    splits = split_blocks(all_blocks)

    write_blocks(PROCESSED_DIR / "corpus.txt", all_blocks)
    write_blocks(PROCESSED_DIR / "train.txt", splits["train"])
    write_blocks(PROCESSED_DIR / "valid.txt", splits["valid"])
    write_blocks(PROCESSED_DIR / "test.txt", splits["test"])

    skipped = skipped_collect + skipped_read
    write_manifest(source_files, source_blocks, qa_blocks, splits, skipped)

    print("Stage 1 dataset generated.")
    print(f"source blocks: {len(source_blocks)}")
    print(f"synthetic QA blocks: {len(qa_blocks)}")
    print(f"total chars: {sum(block.chars for block in all_blocks)}")
    for name in ("train", "valid", "test"):
        stats = split_stats(splits[name])
        print(f"{name}: blocks={stats['blocks']}, chars={stats['chars']}, KiB={stats['kib']}")
    print(f"outputs: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
