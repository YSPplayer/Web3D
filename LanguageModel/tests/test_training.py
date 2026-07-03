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
    adjust_learning_rate_on_plateau,
    estimate_loss,
    get_optimizer_learning_rate,
    load_training_checkpoint,
    read_best_valid_loss,
    resolve_resume_checkpoint,
    restore_training_state,
    save_best_checkpoint_if_improved,
    save_checkpoint,
    should_stop_for_escape_key,
    train_step,
    update_early_stopping,
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

    def test_update_early_stopping_stops_after_patience_without_improvement(self) -> None:
        fresh = update_early_stopping(improved=True, stale_evals=3, patience=2)
        first_stale = update_early_stopping(improved=False, stale_evals=0, patience=2)
        second_stale = update_early_stopping(improved=False, stale_evals=1, patience=2)

        self.assertEqual(fresh.stale_evals, 0)
        self.assertFalse(fresh.should_stop)
        self.assertEqual(first_stale.stale_evals, 1)
        self.assertFalse(first_stale.should_stop)
        self.assertEqual(second_stale.stale_evals, 2)
        self.assertTrue(second_stale.should_stop)
        self.assertIn("valid_loss", second_stale.reason)

    def test_adjust_learning_rate_on_plateau_reduces_optimizer_lr(self) -> None:
        parameter = torch.nn.Parameter(torch.tensor(1.0))
        optimizer = torch.optim.AdamW([parameter], lr=1e-3)

        unchanged = adjust_learning_rate_on_plateau(
            optimizer=optimizer,
            improved=False,
            stale_evals=2,
            patience=3,
            factor=0.5,
            min_lr=1e-5,
        )
        reduced = adjust_learning_rate_on_plateau(
            optimizer=optimizer,
            improved=False,
            stale_evals=3,
            patience=3,
            factor=0.5,
            min_lr=1e-5,
        )
        floor = adjust_learning_rate_on_plateau(
            optimizer=optimizer,
            improved=False,
            stale_evals=6,
            patience=3,
            factor=0.001,
            min_lr=1e-5,
        )

        self.assertFalse(unchanged.reduced)
        self.assertEqual(unchanged.current_lr, 1e-3)
        self.assertTrue(reduced.reduced)
        self.assertAlmostEqual(reduced.current_lr, 5e-4)
        self.assertAlmostEqual(get_optimizer_learning_rate(optimizer), 1e-5)
        self.assertTrue(floor.reduced)
        self.assertIn("learning_rate", floor.reason)

    def test_should_stop_for_escape_key_uses_injected_reader(self) -> None:
        self.assertTrue(should_stop_for_escape_key(lambda: "\x1b"))
        self.assertFalse(should_stop_for_escape_key(lambda: "a"))
        self.assertFalse(should_stop_for_escape_key(lambda: None))

    def test_resolve_resume_checkpoint_supports_explicit_and_auto_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_dir = Path(temp_dir) / "checkpoint"
            checkpoint_dir.mkdir()
            latest_path = checkpoint_dir / "latest.pt"
            explicit_path = Path(temp_dir) / "manual.pt"
            latest_path.write_bytes(b"latest")
            explicit_path.write_bytes(b"manual")

            explicit = resolve_resume_checkpoint(
                checkpoint_dir=checkpoint_dir,
                resume_path=explicit_path,
                auto_resume=True,
            )
            automatic = resolve_resume_checkpoint(
                checkpoint_dir=checkpoint_dir,
                resume_path=None,
                auto_resume=True,
            )
            disabled = resolve_resume_checkpoint(
                checkpoint_dir=checkpoint_dir,
                resume_path=None,
                auto_resume=False,
            )

        self.assertEqual(explicit, explicit_path)
        self.assertEqual(automatic, latest_path)
        self.assertIsNone(disabled)

    def test_load_training_checkpoint_and_restore_training_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GPTConfig(
                vocab_size=17,
                block_size=8,
                n_embd=16,
                n_head=4,
                n_layer=2,
                dropout=0.0,
            )
            dataset = self._make_dataset(temp_dir)
            model = GPTLanguageModel(config)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
            train_step(
                model=model,
                optimizer=optimizer,
                dataset=dataset,
                batch_size=4,
                block_size=config.block_size,
            )
            checkpoint_path = save_checkpoint(
                checkpoint_dir=Path(temp_dir) / "checkpoint",
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4},
                step=9,
                train_loss=1.1,
                valid_loss=1.2,
                checkpoint_name="latest.pt",
            )

            loaded_config, payload = load_training_checkpoint(checkpoint_path, device=torch.device("cpu"))
            restored_model = GPTLanguageModel(loaded_config)
            restored_optimizer = torch.optim.AdamW(restored_model.parameters(), lr=1e-3)
            restored_step = restore_training_state(restored_model, restored_optimizer, payload)

        self.assertEqual(loaded_config.vocab_size, config.vocab_size)
        self.assertEqual(restored_step, 9)
        self.assertTrue(torch.equal(model.token_embedding.weight, restored_model.token_embedding.weight))
        self.assertGreater(len(restored_optimizer.state_dict()["state"]), 0)

    def test_read_best_valid_loss_loads_best_checkpoint_metric(self) -> None:
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
            save_checkpoint(
                checkpoint_dir=checkpoint_dir,
                model=model,
                optimizer=optimizer,
                model_config=config,
                train_config={"batch_size": 4},
                step=3,
                train_loss=1.3,
                valid_loss=0.9,
                checkpoint_name="best.pt",
            )

            best_valid_loss = read_best_valid_loss(checkpoint_dir, device=torch.device("cpu"))

        self.assertEqual(best_valid_loss, 0.9)


if __name__ == "__main__":
    unittest.main()
