from pathlib import Path
import shutil

SKILLS_ROOT = Path("/data/skills")
BUNDLED_SKILLS_ROOT = Path(__file__).resolve().parent / "skills"


def ensure_skills_available():
    if not BUNDLED_SKILLS_ROOT.is_dir():
        raise FileNotFoundError(f"Bundled skills directory not found: {BUNDLED_SKILLS_ROOT}")

    SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    for source_path in BUNDLED_SKILLS_ROOT.rglob("*"):
        if not source_path.is_file():
            continue

        target_path = SKILLS_ROOT / source_path.relative_to(BUNDLED_SKILLS_ROOT)
        if target_path.exists():
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def list_available_skills():
    ensure_skills_available()

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
