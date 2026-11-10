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

    def test_path_name_comparison_can_finalize_without_another_tool_decision(self):
        result = {
            "match_count": 25,
            "items": [{"name": "sample"}],
            "has_more": True,
            "result_complete": True,
        }
        self.assertTrue(self.policy.can_finalize(
            "compare_path_names",
            {},
            result,
        ))

    def test_read_only_result_cannot_finalize_required_delete_operation(self):
        result = {
            "entries": [{"name": "target", "type": "directory"}],
            "directory_count": 1,
            "max_depth": 0,
            "truncated": False,
        }

        self.assertFalse(self.policy.can_finalize(
            "list_directory",
            {"path": "E:\\case_query\\data_out_x3p", "max_depth": 0},
            result,
            request_context={
                "directories_only": True,
                "required_tool_names": ["delete_path"],
            },
        ))


if __name__ == "__main__":
    unittest.main()
