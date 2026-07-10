import sys
import tempfile
import unittest
from pathlib import Path

import torch


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANGUAGE_MODEL_ROOT / "src"))

from lm.dataset import TokenDataset


class TokenDatasetTests(unittest.TestCase):
    def test_get_batch_returns_shifted_long_tensors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ids_path = Path(temp_dir) / "ids.pt"
            torch.save(torch.arange(32, dtype=torch.long), ids_path)

            dataset = TokenDataset(ids_path, device="cpu")
            generator = torch.Generator().manual_seed(123)
            x, y = dataset.get_batch(batch_size=4, block_size=6, generator=generator)

        self.assertEqual(tuple(x.shape), (4, 6))
        self.assertEqual(tuple(y.shape), (4, 6))
        self.assertEqual(x.dtype, torch.long)
        self.assertEqual(y.dtype, torch.long)
        self.assertEqual(x.device.type, "cpu")
        self.assertEqual(y.device.type, "cpu")
        self.assertTrue(torch.equal(x[:, 1:], y[:, :-1]))
        self.assertTrue(torch.all(x[:, 1:] - x[:, :-1] == 1))
        self.assertTrue(torch.all(y[:, 1:] - y[:, :-1] == 1))

    def test_rejects_block_size_that_cannot_build_shifted_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ids_path = Path(temp_dir) / "ids.pt"
            torch.save(torch.arange(4, dtype=torch.long), ids_path)

            dataset = TokenDataset(ids_path, device="cpu")

            with self.assertRaises(ValueError) as context:
                dataset.get_batch(batch_size=1, block_size=4)

        self.assertIn("block_size", str(context.exception))


if __name__ == "__main__":
    unittest.main()
