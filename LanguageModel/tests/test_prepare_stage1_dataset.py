import importlib.util
import sys
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

        self.assertGreaterEqual(len(items), 120)
        self.assertTrue(any(source.startswith("synthetic_programming_zh_qa/") for source in sources))
        self.assertTrue(any(item["question"] == "请问什么是 AI？" for item in items))


if __name__ == "__main__":
    unittest.main()
