from __future__ import annotations

import os
import tarfile
from pathlib import Path


EXCLUDES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "storage",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    ".idea",
    "reskinai_release.tar",
    "tmp_myKey.ppk",
}


def should_include(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in EXCLUDES:
        return False
    for part in parts:
        if part in EXCLUDES:
            return False
    return True


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "reskinai_release.tar"
    if out.exists():
        out.unlink()

    with tarfile.open(out, "w") as tf:
        for path in root.rglob("*"):
            rel = path.relative_to(root)
            if not should_include(rel):
                continue
            # Keep permissions reasonably consistent across OSes.
            tf.add(path, arcname=str(rel).replace(os.sep, "/"), recursive=False)

    print(out)
    print(out.stat().st_size)


if __name__ == "__main__":
    main()

