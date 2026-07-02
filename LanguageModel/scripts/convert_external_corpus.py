from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TextIO


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTERNAL_DOCS_DIR = LANGUAGE_MODEL_ROOT / "data" / "raw" / "external_docs"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def find_text_path(element: ET.Element, *names: str) -> str:
    current: ET.Element | None = element
    for name in names:
        if current is None:
            return ""
        current = find_child(current, name)
    return "" if current is None or current.text is None else current.text


def remove_balanced_markup(text: str, start: str, end: str) -> str:
    result: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        if text.startswith(start, index):
            depth += 1
            index += len(start)
            continue
        if depth > 0 and text.startswith(end, index):
            depth -= 1
            index += len(end)
            continue
        if depth == 0:
            result.append(text[index])
        index += 1
    return "".join(result)


def clean_language_variant(match: re.Match[str]) -> str:
    content = match.group(1)
    parts = [part.strip() for part in content.split(";") if part.strip()]
    preferred_prefixes = ("zh-hans:", "zh-cn:", "zh-sg:", "zh:")
    for prefix in preferred_prefixes:
        for part in parts:
            if part.lower().startswith(prefix):
                return part.split(":", 1)[1].strip()
    if parts:
        return parts[-1].split(":", 1)[-1].strip()
    return ""


def replace_internal_link(match: re.Match[str]) -> str:
    body = match.group(1).strip()
    if not body:
        return ""
    namespace = body.split(":", 1)[0].lower()
    if namespace in {"category", "file", "image", "分类", "分類", "文件", "檔案", "图像", "圖片"}:
        return ""
    parts = [part.strip() for part in body.split("|")]
    label = parts[-1] if len(parts) > 1 and parts[-1] else parts[0]
    return label.split("#", 1)[0].strip()


def clean_mediawiki_markup(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<ref\b[^>/]*/\s*>", "", text, flags=re.I)
    text = re.sub(r"<ref\b[^>]*>.*?</ref>", "", text, flags=re.I | re.S)
    text = re.sub(r"-\{([^{}]{1,500})\}-", clean_language_variant, text)

    # 模板和表格会带来大量非自然语言符号，训练前先剔除。
    text = remove_balanced_markup(text, "{{", "}}")
    text = remove_balanced_markup(text, "{|", "|}")

    text = re.sub(r"\[\[(?:Category|File|Image|分类|分類|文件|檔案|图像|圖片):[^\]]*\]\]", "", text, flags=re.I)
    text = re.sub(r"\[\[([^\[\]]+)\]\]", replace_internal_link, text)
    text = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]]+\]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"^=+\s*(.*?)\s*=+\s*$", r"\1", text, flags=re.M)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("'''", "").replace("''", "")
    text = text.replace("__TOC__", "").replace("__NOTOC__", "")

    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.upper().startswith("#REDIRECT"):
            continue
        if line.startswith(("|", "!", "{|", "|}", "[[Category:", "[[分类:", "[[分類:")):
            continue
        line = re.sub(r"^[*#;:]+\s*", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def count_cjk(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def is_usable_document(text: str, min_chars: int) -> bool:
    if len(text) < min_chars:
        return False
    if count_cjk(text) < max(20, min_chars // 10):
        return False
    bad_chars = sum(1 for char in text if ord(char) < 32 and char not in "\n\t")
    return bad_chars / max(len(text), 1) <= 0.01


def split_text_chunks(text: str, chunk_chars: int) -> list[str]:
    if chunk_chars <= 0 or len(text) <= chunk_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    for paragraph in paragraphs:
        if len(paragraph) > chunk_chars:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_len = 0
            for index in range(0, len(paragraph), chunk_chars):
                chunks.append(paragraph[index : index + chunk_chars].strip())
            continue

        next_len = current_len + len(paragraph) + (2 if current else 0)
        if current and next_len > chunk_chars:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len = next_len

    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def write_record(file: TextIO, record: dict[str, object]) -> None:
    file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
    file.write("\n")


class PartFileWriter:
    def __init__(self, output_dir: Path, output_stem: str, docs_per_file: int) -> None:
        if docs_per_file <= 0:
            raise ValueError("docs_per_file must be greater than 0")
        self.output_dir = output_dir
        self.output_stem = output_stem
        self.docs_per_file = docs_per_file
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.part_index = 0
        self.docs_in_current_part = 0
        self.current_file: TextIO | None = None
        self.paths: list[Path] = []

    def __enter__(self) -> "PartFileWriter":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        if self.current_file is not None:
            self.current_file.close()
            self.current_file = None

    def _open_next_part(self) -> None:
        self.close()
        self.part_index += 1
        self.docs_in_current_part = 0
        path = self.output_dir / f"{self.output_stem}_part_{self.part_index:04d}.jsonl"
        self.current_file = path.open("w", encoding="utf-8")
        self.paths.append(path)

    def write(self, record: dict[str, object]) -> None:
        if self.current_file is None or self.docs_in_current_part >= self.docs_per_file:
            self._open_next_part()
        if self.current_file is None:
            raise RuntimeError("Part file writer is not open")
        write_record(self.current_file, record)
        self.docs_in_current_part += 1


def usable_chunks_for_text(text: str, min_chars: int, chunk_chars: int) -> list[str]:
    return [
        chunk
        for chunk in split_text_chunks(text, chunk_chars=chunk_chars)
        if is_usable_document(chunk, min_chars=min_chars)
    ]


def convert_mediawiki_xml_file(
    input_path: Path,
    output_path: Path,
    source_prefix: str,
    min_chars: int,
    chunk_chars: int,
    max_docs: int,
    append: bool = False,
    start_index: int = 1,
) -> dict[str, int | str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats: dict[str, int | str] = {
        "input": str(input_path),
        "output": str(output_path),
        "pages_seen": 0,
        "pages_skipped": 0,
        "documents_written": 0,
        "next_index": start_index,
    }
    mode = "a" if append else "w"
    serial = start_index

    with output_path.open(mode, encoding="utf-8") as output_file:
        for _, page in ET.iterparse(input_path, events=("end",)):
            if local_name(page.tag) != "page":
                continue

            stats["pages_seen"] = int(stats["pages_seen"]) + 1
            title = find_text_path(page, "title").strip()
            namespace = find_text_path(page, "ns").strip()
            redirect = find_child(page, "redirect") is not None
            raw_text = find_text_path(page, "revision", "text")

            if namespace != "0" or redirect or not raw_text:
                stats["pages_skipped"] = int(stats["pages_skipped"]) + 1
                page.clear()
                continue

            cleaned = clean_mediawiki_markup(raw_text)
            if not is_usable_document(cleaned, min_chars=min_chars):
                stats["pages_skipped"] = int(stats["pages_skipped"]) + 1
                page.clear()
                continue

            for chunk_index, chunk in enumerate(usable_chunks_for_text(cleaned, min_chars, chunk_chars), start=1):
                record = {
                    "schema_version": 1,
                    "source": f"{source_prefix}/{serial:06d}",
                    "language": "zh",
                    "kind": "external_document",
                    "title": title,
                    "chunk_index": chunk_index,
                    "text": chunk,
                }
                write_record(output_file, record)
                serial += 1
                stats["documents_written"] = int(stats["documents_written"]) + 1
                if max_docs > 0 and int(stats["documents_written"]) >= max_docs:
                    stats["next_index"] = serial
                    page.clear()
                    return stats

            page.clear()

    stats["next_index"] = serial
    return stats


def convert_mediawiki_xml_files_to_parts(
    input_paths: list[Path],
    output_dir: Path,
    output_stem: str,
    source_prefix: str,
    min_chars: int,
    chunk_chars: int,
    max_docs: int,
    docs_per_file: int,
) -> dict[str, int | str | list[str]]:
    stats: dict[str, int | str | list[str]] = {
        "output_dir": str(output_dir),
        "output_stem": output_stem,
        "pages_seen": 0,
        "pages_skipped": 0,
        "documents_written": 0,
        "part_files_written": 0,
        "part_files": [],
    }
    serial = 1

    with PartFileWriter(output_dir=output_dir, output_stem=output_stem, docs_per_file=docs_per_file) as writer:
        for input_path in input_paths:
            for _, page in ET.iterparse(input_path, events=("end",)):
                if local_name(page.tag) != "page":
                    continue

                stats["pages_seen"] = int(stats["pages_seen"]) + 1
                title = find_text_path(page, "title").strip()
                namespace = find_text_path(page, "ns").strip()
                redirect = find_child(page, "redirect") is not None
                raw_text = find_text_path(page, "revision", "text")

                if namespace != "0" or redirect or not raw_text:
                    stats["pages_skipped"] = int(stats["pages_skipped"]) + 1
                    page.clear()
                    continue

                cleaned = clean_mediawiki_markup(raw_text)
                if not is_usable_document(cleaned, min_chars=min_chars):
                    stats["pages_skipped"] = int(stats["pages_skipped"]) + 1
                    page.clear()
                    continue

                for chunk_index, chunk in enumerate(usable_chunks_for_text(cleaned, min_chars, chunk_chars), start=1):
                    record = {
                        "schema_version": 1,
                        "source": f"{source_prefix}/{serial:06d}",
                        "language": "zh",
                        "kind": "external_document",
                        "title": title,
                        "chunk_index": chunk_index,
                        "text": chunk,
                    }
                    writer.write(record)
                    serial += 1
                    stats["documents_written"] = int(stats["documents_written"]) + 1
                    if max_docs > 0 and int(stats["documents_written"]) >= max_docs:
                        page.clear()
                        stats["part_files_written"] = len(writer.paths)
                        stats["part_files"] = [str(path) for path in writer.paths]
                        return stats

                page.clear()

        stats["part_files_written"] = len(writer.paths)
        stats["part_files"] = [str(path) for path in writer.paths]
        return stats


def input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(path for path in input_path.rglob("*") if path.is_file())
    raise FileNotFoundError(f"Input path does not exist: {input_path}")


def default_output_path(input_path: Path) -> Path:
    stem = input_path.name.rstrip("\\/")
    return DEFAULT_EXTERNAL_DOCS_DIR / f"{stem}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert external corpora into stage1 external_document JSONL.")
    parser.add_argument("--input", type=Path, required=True, help="MediaWiki XML file, or a directory containing XML files.")
    parser.add_argument("--output", type=Path, default=None, help="Output JSONL path. Defaults to data/raw/external_docs/<input>.jsonl.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXTERNAL_DOCS_DIR, help="Directory used when --docs-per-file is greater than 0.")
    parser.add_argument("--output-stem", default=None, help="Output file prefix used with --docs-per-file.")
    parser.add_argument("--type", choices=["mediawiki_xml"], default="mediawiki_xml")
    parser.add_argument("--source-prefix", default="zhwiki", help="Prefix used in generated source ids.")
    parser.add_argument("--min-chars", type=int, default=120)
    parser.add_argument("--chunk-chars", type=int, default=2000)
    parser.add_argument("--max-docs", type=int, default=0, help="Use 0 to convert all usable documents.")
    parser.add_argument("--docs-per-file", type=int, default=0, help="Split output into part JSONL files with this many documents per file. Use 0 for one JSONL.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = input_files(args.input)
    output_path = args.output or default_output_path(args.input)
    if args.docs_per_file > 0:
        output_stem = args.output_stem or output_path.stem
        summary = convert_mediawiki_xml_files_to_parts(
            input_paths=paths,
            output_dir=args.output_dir,
            output_stem=output_stem,
            source_prefix=args.source_prefix,
            min_chars=args.min_chars,
            chunk_chars=args.chunk_chars,
            max_docs=args.max_docs,
            docs_per_file=args.docs_per_file,
        )
        summary.update(
            {
                "input": str(args.input),
                "files_seen": len(paths),
                "source_prefix": args.source_prefix,
                "min_chars": args.min_chars,
                "chunk_chars": args.chunk_chars,
                "max_docs": args.max_docs,
                "docs_per_file": args.docs_per_file,
            }
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    combined_stats: list[dict[str, int | str]] = []
    next_index = 1
    remaining_max_docs = args.max_docs

    for index, path in enumerate(paths):
        if remaining_max_docs == 0 and args.max_docs > 0:
            break
        stats = convert_mediawiki_xml_file(
            input_path=path,
            output_path=output_path,
            source_prefix=args.source_prefix,
            min_chars=args.min_chars,
            chunk_chars=args.chunk_chars,
            max_docs=remaining_max_docs,
            append=index > 0,
            start_index=next_index,
        )
        combined_stats.append(stats)
        next_index = int(stats["next_index"])
        if args.max_docs > 0:
            remaining_max_docs -= int(stats["documents_written"])

    summary = {
        "input": str(args.input),
        "output": str(output_path),
        "files_seen": len(paths),
        "pages_seen": sum(int(item["pages_seen"]) for item in combined_stats),
        "pages_skipped": sum(int(item["pages_skipped"]) for item in combined_stats),
        "documents_written": sum(int(item["documents_written"]) for item in combined_stats),
        "source_prefix": args.source_prefix,
        "min_chars": args.min_chars,
        "chunk_chars": args.chunk_chars,
        "max_docs": args.max_docs,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
