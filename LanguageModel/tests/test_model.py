import sys
import unittest
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.model import GPTConfig, GPTLanguageModel


class GPTLanguageModelTests(unittest.TestCase):
    def test_forward_returns_logits_and_scalar_loss(self) -> None:
        config = GPTConfig(
            vocab_size=23,
            block_size=8,
            n_embd=16,
            n_head=4,
            n_layer=2,
            dropout=0.0,
        )
        model = GPTLanguageModel(config)
        x = torch.randint(0, config.vocab_size, (3, config.block_size), dtype=torch.long)
        y = torch.randint(0, config.vocab_size, (3, config.block_size), dtype=torch.long)

        logits, loss = model(x, y)

        self.assertEqual(tuple(logits.shape), (3, config.block_size, config.vocab_size))
        self.assertIsNotNone(loss)
        self.assertEqual(tuple(loss.shape), ())
        self.assertTrue(torch.isfinite(loss))

    def test_forward_rejects_sequence_longer_than_block_size(self) -> None:
        config = GPTConfig(
            vocab_size=23,
            block_size=8,
            n_embd=16,
            n_head=4,
            n_layer=2,
            dropout=0.0,
        )
        model = GPTLanguageModel(config)
        x = torch.randint(0, config.vocab_size, (2, config.block_size + 1), dtype=torch.long)

        with self.assertRaises(ValueError) as context:
            model(x)

        self.assertIn("block_size", str(context.exception))

    def test_generate_extends_context_with_token_ids(self) -> None:
        torch.manual_seed(123)
        config = GPTConfig(
            vocab_size=23,
            block_size=8,
            n_embd=16,
            n_head=4,
            n_layer=2,
            dropout=0.0,
        )
        model = GPTLanguageModel(config)
        model.eval()
        context = torch.tensor([[1, 2, 3]], dtype=torch.long)

        generated = model.generate(context, max_new_tokens=5)

        self.assertEqual(tuple(generated.shape), (1, 8))
        self.assertEqual(generated.dtype, torch.long)
        self.assertTrue(torch.equal(generated[:, :3], context))
        self.assertTrue(torch.all(generated >= 0))
        self.assertTrue(torch.all(generated < config.vocab_size))

    def test_config_requires_attention_heads_to_divide_embedding_size(self) -> None:
        with self.assertRaises(ValueError) as context:
            GPTConfig(
                vocab_size=23,
                block_size=8,
                n_embd=18,
                n_head=4,
                n_layer=2,
            )

        self.assertIn("n_embd", str(context.exception))


if __name__ == "__main__":
    unittest.main()
