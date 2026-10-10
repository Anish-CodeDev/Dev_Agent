from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parent / "skills"


def list_available_skills():
    if not SKILLS_ROOT.is_dir():
        return []

    skills = []
    skills_root = SKILLS_ROOT.resolve()
    for path in SKILLS_ROOT.rglob("*.md"):
        if path.name == "skill_template.md" or not path.is_file():
            continue
        try:
            path.resolve().relative_to(skills_root)
        except (OSError, ValueError):
            continue
        skills.append(path.relative_to(SKILLS_ROOT).as_posix())
    return sorted(skills, key=str.casefold)


def read_skill_content(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252")
