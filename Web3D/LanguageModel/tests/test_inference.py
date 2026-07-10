import sys
import tempfile
import unittest
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.inference import (
    build_qa_prompt,
    extract_answer,
    generate_token_ids,
    load_model_from_checkpoint,
)
from lm.model import GPTConfig, GPTLanguageModel


class FakeAutoregressiveModel:
    def __init__(self, token_ids: list[int], vocab_size: int = 16, block_size: int = 8) -> None:
        self.config = type("Config", (), {"block_size": block_size})()
        self.token_ids = token_ids
        self.vocab_size = vocab_size
        self.calls = 0

    def eval(self) -> "FakeAutoregressiveModel":
        return self

    def __call__(self, idx: torch.Tensor) -> tuple[torch.Tensor, None]:
        next_id = self.token_ids[min(self.calls, len(self.token_ids) - 1)]
        self.calls += 1
        logits = torch.full(
            (idx.shape[0], idx.shape[1], self.vocab_size),
            -1000.0,
            device=idx.device,
        )
        logits[:, -1, next_id] = 1000.0
        return logits, None


class InferenceTests(unittest.TestCase):
    def test_build_qa_prompt_matches_training_text_format(self) -> None:
        prompt = build_qa_prompt(" 什么是 AdamW？ ")

        self.assertEqual(prompt, "<|qa_start|>\n问题：什么是 AdamW？\n回答：")

    def test_build_qa_prompt_rejects_empty_question(self) -> None:
        with self.assertRaises(ValueError):
            build_qa_prompt("   ")

    def test_extract_answer_returns_text_after_answer_marker_and_stops_at_qa_end(self) -> None:
        decoded = "<|qa_start|>\n问题：x\n回答：第一句。\n第二句。\n<|qa_end|>后面的内容"

        answer = extract_answer(decoded)

        self.assertEqual(answer, "第一句。\n第二句。")

    def test_generate_token_ids_stops_when_stop_token_is_generated(self) -> None:
        model = FakeAutoregressiveModel([4, 5, 8, 9])

        ids = generate_token_ids(
            model=model,
            input_ids=[1, 2, 3],
            max_new_tokens=8,
            temperature=0.0,
            top_k=None,
            stop_ids={8},
            device=torch.device("cpu"),
        )

        self.assertEqual(ids, [1, 2, 3, 4, 5, 8])

    def test_load_model_from_checkpoint_rebuilds_model_and_uses_eval_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GPTConfig(
                vocab_size=19,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            original_model = GPTLanguageModel(config)
            checkpoint_path = Path(temp_dir) / "model.pt"
            torch.save(
                {
                    "step": 7,
                    "model_config": config.__dict__,
                    "model_state_dict": original_model.state_dict(),
                },
                checkpoint_path,
            )

            loaded_model, loaded_config, payload = load_model_from_checkpoint(
                checkpoint_path,
                device=torch.device("cpu"),
            )

        self.assertIsInstance(loaded_model, GPTLanguageModel)
        self.assertEqual(loaded_config.vocab_size, 19)
        self.assertEqual(payload["step"], 7)
        self.assertFalse(loaded_model.training)


if __name__ == "__main__":
    unittest.main()
