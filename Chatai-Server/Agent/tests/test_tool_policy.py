import unittest
from pathlib import Path

from Agent.exceptions import ToolPermissionError
from Agent.tool_policy import resolve_allowed_path


class ToolPathPolicyTests(unittest.TestCase):
    def test_wildcard_allows_existing_path(self):
        directory = Path.cwd()
        result = resolve_allowed_path(
            str(directory),
            (Path("*"),),
            must_exist=True,
            require_directory=True,
        )

        self.assertEqual(result, directory.resolve())

    def test_empty_roots_still_denies_path(self):
        with self.assertRaises(ToolPermissionError):
            resolve_allowed_path(str(Path.cwd()), tuple(), must_exist=True)

    def test_wildcard_cannot_be_mixed_with_specific_root(self):
        directory = Path.cwd()
        with self.assertRaises(ToolPermissionError):
            resolve_allowed_path(
                str(directory),
                (Path("*"), directory),
                must_exist=True,
            )

    def test_specific_root_still_rejects_other_directory(self):
        allowed_directory = Path.cwd() / "Agent"
        other_directory = Path.cwd() / "Sql"
        with self.assertRaises(ToolPermissionError):
            resolve_allowed_path(
                str(other_directory),
                (allowed_directory,),
                must_exist=True,
            )


if __name__ == "__main__":
    unittest.main()
