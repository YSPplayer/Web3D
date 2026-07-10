import sys
import tempfile
import unittest
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.tokenizer_builder import SPECIAL_TOKENS, build_char_tokenizer_data, write_char_tokenizer


class TokenizerBuilderTests(unittest.TestCase):
    def test_build_char_tokenizer_keeps_special_token_ids_stable(self) -> None:
        data = build_char_tokenizer_data("问题：请问什么是 AI？\n回答：AI 是人工智能。")

        self.assertEqual(data["name"], "char_v1")
        self.assertEqual(data["special_tokens"]["<pad>"], 0)
        self.assertEqual(data["special_tokens"]["<|qa_start|>"], 7)
        self.assertEqual(data["special_tokens"]["<|qa_end|>"], 8)
        self.assertIn("请", data["token_to_id"])
        self.assertIn("AI", "问题：请问什么是 AI？")
        self.assertEqual(len(SPECIAL_TOKENS), 9)

    def test_write_char_tokenizer_writes_tokenizer_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "char_v1"

            tokenizer_path, summary_path = write_char_tokenizer(
                corpus_text="问题：什么是过拟合？\n回答：过拟合是训练集好但验证集差。",
                output_dir=output_dir,
                source_corpus_bytes=128,
            )

            self.assertEqual(tokenizer_path.name, "tokenizer.json")
            self.assertEqual(summary_path.name, "summary.json")
            self.assertTrue(tokenizer_path.exists())
            self.assertTrue(summary_path.exists())


if __name__ == "__main__":
    unittest.main()
