import unittest

from Agent.skill_loader import AgentSkillLoader


class AgentSkillLoaderTests(unittest.TestCase):
    def test_default_agent_skill_loads_and_is_cached(self):
        loader = AgentSkillLoader()

        first = loader.load()
        second = loader.get()

        self.assertEqual(first.name, "chatai_agent_tool_use")
        self.assertEqual(first.version, "1.0.1")
        self.assertEqual(len(first.content_hash), 64)
        self.assertIs(first, second)
        self.assertIn("必须调用工具的场景", first.content)


if __name__ == "__main__":
    unittest.main()
