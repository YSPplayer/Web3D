import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.dataset import TokenDataset
from lm.model import GPTConfig, GPTLanguageModel
from lm.training import (
    append_metrics_history,
    estimate_loss,
    save_best_checkpoint_if_improved,
    save_checkpoint,
    train_step,
)


class TrainingTests(unittest.TestCase):
    def _make_dataset(self, temp_dir: str, vocab_size: int = 17) -> TokenDataset:
        ids_path = Path(temp_dir) / "ids.pt"
        tokens = torch.arange(160, dtype=torch.long) % vocab_size
        torch.save(tokens, ids_path)
        return TokenDataset(ids_path, device="cpu")

    def test_train_step_updates_model_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = self._make_dataset(temp_dir)
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            model = GPTLanguageModel(config)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
            before = model.token_embedding.weight.detach().clone()

            loss = train_step(
                model=model,
                optimizer=optimizer,
                dataset=dataset,
                batch_size=4,
                block_size=config.block_size,
                generator=torch.Generator().manual_seed(123),
            )

        self.assertIsInstance(loss, float)
        self.assertTrue(torch.isfinite(torch.tensor(loss)))
        self.assertFalse(torch.equal(before, model.token_embedding.weight.detach()))

    def test_estimate_loss_returns_finite_float_and_restores_training_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = self._make_dataset(temp_dir)
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            model = GPTLanguageModel(config)
            model.train()

            loss = estimate_loss(
                model=model,
                dataset=dataset,
                batch_size=4,
                block_size=config.block_size,
                eval_iters=3,
                generator=torch.Generator().manual_seed(456),
            )

        self.assertIsInstance(loss, float)
        self.assertTrue(torch.isfinite(torch.tensor(loss)))
        self.assertTrue(model.training)

    def test_save_checkpoint_writes_model_optimizer_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            model = GPTLanguageModel(config)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
            checkpoint_dir = Path(temp_dir) / "checkpoint"

            checkpoint_path = save_checkpoint(
                checkpoint_dir=checkpoint_dir,
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4, "learning_rate": 1e-3},
                step=5,
                train_loss=1.23,
                valid_loss=1.45,
            )

            metadata_path = checkpoint_dir / "training_config.json"
            payload = torch.load(checkpoint_path, map_location="cpu")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(checkpoint_path.name, "model.pt")
        self.assertEqual(payload["step"], 5)
        self.assertIn("model_state_dict", payload)
        self.assertIn("optimizer_state_dict", payload)
        self.assertEqual(metadata["model_config"]["vocab_size"], 17)
        self.assertEqual(metadata["train_config"]["batch_size"], 4)
        self.assertEqual(metadata["metrics"]["valid_loss"], 1.45)

    def test_save_checkpoint_can_write_named_checkpoint_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            model = GPTLanguageModel(config)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

            checkpoint_path = save_checkpoint(
                checkpoint_dir=Path(temp_dir) / "checkpoint",
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4},
                step=6,
                train_loss=1.11,
                valid_loss=1.22,
                checkpoint_name="latest.pt",
            )
            payload = torch.load(checkpoint_path, map_location="cpu")

        self.assertEqual(checkpoint_path.name, "latest.pt")
        self.assertEqual(payload["step"], 6)
        self.assertEqual(payload["metrics"]["valid_loss"], 1.22)

    def test_save_best_checkpoint_only_when_valid_loss_improves(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            model = GPTLanguageModel(config)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
            checkpoint_dir = Path(temp_dir) / "checkpoint"

            best_loss, improved, checkpoint_path = save_best_checkpoint_if_improved(
                checkpoint_dir=checkpoint_dir,
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4},
                step=1,
                train_loss=2.0,
                valid_loss=1.0,
                best_valid_loss=None,
            )
            unchanged_loss, unchanged, skipped_path = save_best_checkpoint_if_improved(
                checkpoint_dir=checkpoint_dir,
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4},
                step=2,
                train_loss=1.8,
                valid_loss=1.1,
                best_valid_loss=best_loss,
            )
            payload = torch.load(checkpoint_path, map_location="cpu")

        self.assertEqual(best_loss, 1.0)
        self.assertTrue(improved)
        self.assertEqual(checkpoint_path.name, "best.pt")
        self.assertEqual(payload["step"], 1)
        self.assertEqual(payload["metrics"]["valid_loss"], 1.0)
        self.assertEqual(unchanged_loss, 1.0)
        self.assertFalse(unchanged)
        self.assertIsNone(skipped_path)

    def test_append_metrics_history_writes_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "metrics_history.jsonl"

            append_metrics_history(
                history_path,
                {"step": 1, "train_loss": 2.0, "valid_loss": 1.5, "is_best": True},
            )
            append_metrics_history(
                history_path,
                {"step": 2, "train_loss": 1.8, "valid_loss": 1.6, "is_best": False},
            )
            lines = history_path.read_text(encoding="utf-8").splitlines()
            records = [json.loads(line) for line in lines]

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["step"], 1)
        self.assertTrue(records[0]["is_best"])
        self.assertFalse(records[1]["is_best"])


if __name__ == "__main__":
    unittest.main()
