import sys
import unittest
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.tokenizer import CharTokenizer


TOKENIZER_PATH = LANGUAGE_MODEL_ROOT / "data" / "tokenizer" / "char_v1" / "tokenizer.json"


class CharTokenizerTests(unittest.TestCase):
    def test_loads_vocabulary_metadata(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)

        self.assertEqual(tokenizer.name, "char_v1")
        self.assertEqual(tokenizer.vocab_size, 1027)
        self.assertEqual(tokenizer.pad_id, 0)
        self.assertEqual(tokenizer.unk_id, 1)
        self.assertEqual(tokenizer.bos_id, 2)
        self.assertEqual(tokenizer.eos_id, 3)
        self.assertEqual(tokenizer.special_tokens["<|qa_start|>"], 7)
        self.assertEqual(tokenizer.special_tokens["<|qa_end|>"], 8)

    def test_encodes_special_tokens_as_single_ids(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)
        text = "<|qa_start|>\n问题：AdamW 和 SGD 有什么区别？\n回答：使用 AdamW。\n<|qa_end|>"

        ids = tokenizer.encode(text)

        self.assertEqual(ids[0], tokenizer.special_tokens["<|qa_start|>"])
        self.assertEqual(ids[-1], tokenizer.special_tokens["<|qa_end|>"])
        self.assertLess(len(ids), len(text))
        self.assertEqual(tokenizer.decode(ids), text)

    def test_encodes_regular_text_character_by_character(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)
        text = "int add(int a, int b) { return a + b; }"

        ids = tokenizer.encode(text)

        self.assertEqual(len(ids), len(text))
        self.assertEqual(tokenizer.decode(ids), text)

    def test_unknown_character_uses_unk_id(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)

        ids = tokenizer.encode("\U0001f9ea")

        self.assertEqual(ids, [tokenizer.unk_id])
        self.assertEqual(tokenizer.decode(ids), "<unk>")

    def test_prints_encode_decode_demo(self) -> None:
        tokenizer = CharTokenizer.from_file(TOKENIZER_PATH)
        text = "<|qa_start|>\n问题：什么是 AdamW？\n回答：AdamW 是常用优化器。\n<|qa_end|>"

        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        print("\n[CharTokenizer encode/decode demo]")
        print(f"raw text:\n{text}")
        print(f"ids length: {len(ids)}")
        print(f"ids prefix: {ids[:40]}")
        print(f"decoded text:\n{decoded}")

        self.assertEqual(ids[0], tokenizer.special_tokens["<|qa_start|>"])
        self.assertEqual(ids[-1], tokenizer.special_tokens["<|qa_end|>"])
        self.assertEqual(decoded, text)


if __name__ == "__main__":
    unittest.main()
