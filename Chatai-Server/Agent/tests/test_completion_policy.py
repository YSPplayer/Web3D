import unittest

from Agent.completion_policy import ToolCompletionPolicy


class ToolCompletionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = ToolCompletionPolicy()

    def test_complete_direct_directory_result_can_finalize(self):
        result = {
            "entries": [
                {"name": "a", "type": "directory"},
                {"name": "b", "type": "directory"},
            ],
            "directory_count": 2,
            "max_depth": 0,
            "truncated": False,
        }

        self.assertTrue(self.policy.can_finalize(
            "list_directory",
            {"path": "D:\\MeasResults", "max_depth": 0},
            result,
            request_context={"directories_only": True},
        ))

    def test_truncated_or_mixed_directory_result_cannot_finalize(self):
        truncated = {
            "entries": [{"name": "a", "type": "directory"}],
            "directory_count": 1,
            "truncated": True,
        }
        mixed = {
            "entries": [
                {"name": "a", "type": "directory"},
                {"name": "file.txt", "type": "file"},
            ],
            "directory_count": 1,
            "truncated": False,
        }

        self.assertFalse(self.policy.can_finalize(
            "list_directory",
            {"path": "D:\\MeasResults", "max_depth": 0},
            truncated,
            request_context={"directories_only": True},
        ))
        self.assertFalse(self.policy.can_finalize(
            "list_directory",
            {"path": "D:\\MeasResults", "max_depth": 0},
            mixed,
            request_context={"directories_only": True},
        ))


if __name__ == "__main__":
    unittest.main()
