import unittest
from unittest.mock import patch

from Model.token_manager import TokenManager


class TokenManagerTests(unittest.TestCase):
    def test_litellm_metadata_is_used_and_database_overrides_it(self):
        manager = TokenManager()
        runtime = {
            "is_local_model": False,
            "model_name": "openai/test",
        }
        with patch(
            "Model.token_manager.litellm.get_model_info",
            return_value={
                "max_input_tokens": 128_000,
                "max_output_tokens": 8_192,
            },
        ):
            metadata_profile = manager.resolve_profile(runtime, {})
            override_profile = manager.resolve_profile(runtime, {
                "context_window": 64_000,
                "max_output_tokens": 4_096,
                "safety_margin_tokens": 1_024,
            })

        self.assertEqual(metadata_profile.context_window, 128_000)
        self.assertEqual(metadata_profile.max_output_tokens, 8_192)
        self.assertEqual(override_profile.context_window, 64_000)
        self.assertEqual(override_profile.max_output_tokens, 4_096)
        self.assertEqual(override_profile.safety_margin_tokens, 1_024)

    def test_input_budget_reserves_output_and_safety_margin(self):
        manager = TokenManager()
        with patch(
            "Model.token_manager.litellm.get_model_info",
            return_value={
                "max_input_tokens": 32_768,
                "max_output_tokens": 1_024,
            },
        ):
            profile = manager.resolve_profile(
                {"is_local_model": False, "model_name": "test/model"},
                {"safety_margin_tokens": 512},
            )

        self.assertEqual(profile.input_budget, 31_232)


if __name__ == "__main__":
    unittest.main()
