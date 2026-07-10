import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_SCRIPT = LANGUAGE_MODEL_ROOT / "scripts" / "convert_external_corpus.py"


def load_converter_module():
    spec = importlib.util.spec_from_file_location("convert_external_corpus", CONVERTER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {CONVERTER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ConvertExternalCorpusTests(unittest.TestCase):
    def test_clean_mediawiki_markup_removes_wiki_syntax_and_keeps_chinese_text(self) -> None:
        module = load_converter_module()

        raw = (
            "[[File:Example.jpg|thumb|这是一段图片说明]]\n"
            "'''人工智能'''是研究智能系统的领域。{{Infobox|name=AI}}\n"
            "它和[[机器学习|机器学习]]、[[深度学习]]有关。<ref>引用内容</ref>\n"
            "[https://example.com 外部资料]\n"
            "[[Category:人工智能]]"
        )
        cleaned = module.clean_mediawiki_markup(raw)

        self.assertIn("人工智能是研究智能系统的领域。", cleaned)
        self.assertIn("机器学习", cleaned)
        self.assertIn("深度学习", cleaned)
        self.assertIn("外部资料", cleaned)
        self.assertNotIn("{{", cleaned)
        self.assertNotIn("<ref>", cleaned)
        self.assertNotIn("Category", cleaned)
        self.assertNotIn("图片说明", cleaned)

    def test_convert_mediawiki_xml_file_writes_external_document_jsonl(self) -> None:
        module = load_converter_module()
        mediawiki_xml = """<?xml version="1.0" encoding="utf-8"?>
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
  <page>
    <title>人工智能</title>
    <ns>0</ns>
    <revision>
      <text>'''人工智能'''是研究智能系统的领域。它可以用于问答、规划和代码辅助。[[机器学习|机器学习]]是相关方向。</text>
    </revision>
  </page>
  <page>
    <title>重定向页</title>
    <ns>0</ns>
    <redirect title="人工智能" />
    <revision><text>#REDIRECT [[人工智能]]</text></revision>
  </page>
  <page>
    <title>Talk:人工智能</title>
    <ns>1</ns>
    <revision><text>讨论页不应该进入训练数据。</text></revision>
  </page>
</mediawiki>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.xml"
            output_path = Path(temp_dir) / "docs.jsonl"
            input_path.write_text(mediawiki_xml, encoding="utf-8")

            stats = module.convert_mediawiki_xml_file(
                input_path=input_path,
                output_path=output_path,
                source_prefix="testwiki",
                min_chars=20,
                chunk_chars=200,
                max_docs=0,
            )
            records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(stats["pages_seen"], 3)
        self.assertEqual(stats["documents_written"], 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source"], "testwiki/000001")
        self.assertEqual(records[0]["language"], "zh")
        self.assertEqual(records[0]["kind"], "external_document")
        self.assertEqual(records[0]["title"], "人工智能")
        self.assertIn("人工智能是研究智能系统的领域。", records[0]["text"])

    def test_convert_mediawiki_xml_file_skips_too_short_trailing_chunks(self) -> None:
        module = load_converter_module()
        long_text = "人工智能" * 27
        mediawiki_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
  <page>
    <title>人工智能</title>
    <ns>0</ns>
    <revision><text>{long_text}</text></revision>
  </page>
</mediawiki>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.xml"
            output_path = Path(temp_dir) / "docs.jsonl"
            input_path.write_text(mediawiki_xml, encoding="utf-8")

            stats = module.convert_mediawiki_xml_file(
                input_path=input_path,
                output_path=output_path,
                source_prefix="testwiki",
                min_chars=20,
                chunk_chars=50,
                max_docs=0,
            )
            records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(stats["documents_written"], 2)
        self.assertTrue(all(len(record["text"]) >= 20 for record in records))

    def test_convert_mediawiki_xml_files_can_split_output_by_document_count(self) -> None:
        module = load_converter_module()
        pages = []
        for index in range(5):
            pages.append(
                f"""
  <page>
    <title>条目{index}</title>
    <ns>0</ns>
    <revision><text>人工智能让机器完成智能任务。这是第{index}个测试条目，内容用于验证分片输出。</text></revision>
  </page>"""
            )
        mediawiki_xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
            + "".join(pages)
            + "\n</mediawiki>\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.xml"
            output_dir = Path(temp_dir) / "parts"
            input_path.write_text(mediawiki_xml, encoding="utf-8")

            stats = module.convert_mediawiki_xml_files_to_parts(
                input_paths=[input_path],
                output_dir=output_dir,
                output_stem="wiki_sample",
                source_prefix="testwiki",
                min_chars=20,
                chunk_chars=200,
                max_docs=0,
                docs_per_file=2,
            )
            part_paths = sorted(output_dir.glob("wiki_sample_part_*.jsonl"))
            counts = [len(path.read_text(encoding="utf-8").splitlines()) for path in part_paths]

        self.assertEqual(stats["documents_written"], 5)
        self.assertEqual(stats["part_files_written"], 3)
        self.assertEqual(counts, [2, 2, 1])


if __name__ == "__main__":
    unittest.main()
