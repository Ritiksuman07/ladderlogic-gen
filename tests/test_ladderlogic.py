import unittest

import ladderlogic


class LadderLogicGenerationTests(unittest.TestCase):
    def test_nested_or_expands_to_multiple_rungs(self):
        parsed = ladderlogic.parse_logic_line("IF Start AND (A OR B) THEN Motor")
        self.assertIsNotNone(parsed)
        expr, outputs = parsed
        ladder = ladderlogic.generate_ladder(expr, outputs, "siemens")
        self.assertEqual(ladder.count("// Rung"), 2)
        self.assertIn("[ ] Start----[ ] A", ladder)
        self.assertIn("[ ] Start----[ ] B", ladder)


if __name__ == "__main__":
    unittest.main()
