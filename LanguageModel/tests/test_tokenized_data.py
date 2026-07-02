import sys
import tempfile
import unittest
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.tokenizer import CharTokenizer
from lm.tokenized_data import encode_text_file, save_token_ids_pt


TOKENIZER_PATH = LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1" / "tokenizer.json"


class TokenizedDataTests(unittest.TestCase):
    def test_encode_text_file_returns_one_dimensional_ids(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)
        text = "<|qa_start|>\n问题：什么是 AdamW？\n回答：优化器。\n<|qa_end|>"

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.txt"
            input_path.write_text(text, encoding="utf-8")

            ids = encode_text_file(input_path, tokenizer)

        self.assertIsInstance(ids, list)
        self.assertTrue(all(isinstance(token_id, int) for token_id in ids))
        self.assertEqual(ids[0], tokenizer.special_tokens["<|qa_start|>"])
        self.assertEqual(ids[-1], tokenizer.special_tokens["<|qa_end|>"])
        self.assertEqual(tokenizer.decode(ids), text)

    def test_save_token_ids_pt_requires_torch_or_writes_long_tensor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample_ids.pt"

            try:
                import torch
            except ModuleNotFoundError:
                with self.assertRaises(RuntimeError) as context:
                    save_token_ids_pt([7, 10, 8], output_path)

                self.assertIn("PyTorch is required", str(context.exception))
                self.assertFalse(output_path.exists())
                return

            save_token_ids_pt([7, 10, 8], output_path)
            tensor = torch.load(output_path)
            self.assertEqual(tuple(tensor.shape), (3,))
            self.assertEqual(tensor.dtype, torch.long)
            self.assertEqual(tensor.tolist(), [7, 10, 8])


if __name__ == "__main__":
    unittest.main()
