import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = LANGUAGE_MODEL_ROOT / "scripts" / "train_stage1_gpt.py"


def load_train_module():
    spec = importlib.util.spec_from_file_location("train_stage1_gpt", TRAIN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {TRAIN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TrainStage1GptCliTests(unittest.TestCase):
    def test_default_cli_disables_automatic_early_stopping(self) -> None:
        module = load_train_module()

        with patch.object(sys, "argv", ["train_stage1_gpt.py"]):
            args = module.parse_args()

        self.assertEqual(args.early_stop_patience, 0)


if __name__ == "__main__":
    unittest.main()
