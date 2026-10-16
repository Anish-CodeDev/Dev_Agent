import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import skill_library


class SkillLibraryTests(unittest.TestCase):
    def test_list_seeds_bundled_skills_without_overwriting_persisted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundled = root / "bundled"
            persisted = root / "data" / "skills"
            (bundled / "nested").mkdir(parents=True)
            (bundled / "nested" / "example_skill.md").write_text(
                "Bundled content", encoding="utf-8"
            )
            (bundled / "skill_template.md").write_text(
                "Template content", encoding="utf-8"
            )
            persisted.mkdir(parents=True)
            (persisted / "nested").mkdir()
            (persisted / "nested" / "example_skill.md").write_text(
                "Persisted content", encoding="utf-8"
            )

            with (
                patch.object(skill_library, "BUNDLED_SKILLS_ROOT", bundled),
                patch.object(skill_library, "SKILLS_ROOT", persisted),
            ):
                self.assertEqual(
                    skill_library.list_available_skills(),
                    ["nested/example_skill.md"],
                )

            self.assertEqual(
                (persisted / "nested" / "example_skill.md").read_text(encoding="utf-8"),
                "Persisted content",
            )
            self.assertEqual(
                (persisted / "skill_template.md").read_text(encoding="utf-8"),
                "Template content",
            )


if __name__ == "__main__":
    unittest.main()
