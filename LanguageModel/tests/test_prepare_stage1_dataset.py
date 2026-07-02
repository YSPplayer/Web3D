import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = LANGUAGE_MODEL_ROOT / "scripts" / "prepare_stage1_dataset.py"


def load_prepare_module():
    spec = importlib.util.spec_from_file_location("prepare_stage1_dataset", PREPARE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {PREPARE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrepareStage1DatasetTests(unittest.TestCase):
    def test_loads_all_synthetic_qa_json_files(self) -> None:
        module = load_prepare_module()

        items = module.load_synthetic_qa_items()
        sources = {str(item["source"]) for item in items}

        self.assertGreaterEqual(len(items), 9000)
        self.assertTrue(any(source.startswith("synthetic_programming_zh_qa/") for source in sources))
        self.assertTrue(any(source.startswith("synthetic_zh_qa_3000/") for source in sources))
        self.assertTrue(any(source.startswith("synthetic_dialogue_zh_qa_6000/") for source in sources))
        self.assertTrue(any(item["question"] == "请问什么是 AI？" for item in items))

    def test_loads_external_document_jsonl_files(self) -> None:
        module = load_prepare_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs.jsonl"
            docs = [
                {
                    "source": "external/wiki/000001",
                    "language": "zh",
                    "kind": "external_document",
                    "title": "人工智能",
                    "text": "人工智能是研究智能系统的领域。",
                },
                {
                    "source": "external/wiki/000002",
                    "title": "机器学习",
                    "text": "机器学习让模型从数据中学习规律。",
                },
            ]
            docs_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in docs) + "\n",
                encoding="utf-8",
            )

            items = module.load_external_doc_items(docs_path)
            blocks = module.make_external_doc_blocks(docs_path)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[1]["language"], "zh")
        self.assertEqual(items[1]["kind"], "external_document")
        self.assertEqual(len(blocks), 2)
        self.assertIn("<|file_start|>", blocks[0].text)
        self.assertIn("kind: external_document", blocks[0].text)
        self.assertIn("title: 人工智能", blocks[0].text)
        self.assertIn("<|file_content|>\n人工智能是研究智能系统的领域。", blocks[0].text)


if __name__ == "__main__":
    unittest.main()
