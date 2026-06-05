from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [
    ROOT / "src" / "fastaction",
    ROOT / "tests" / "fastaction",
    ROOT / "docs",
    ROOT / "frontend" / "workbench" / "src",
]
FORBIDDEN = [
    "libs.common",
    "src.core",
    "src.infrastructure",
    "src.fastaction",
    "AH House",
    "AHouse",
    "ah-house",
    "ahouse",
    "装修",
    "图纸",
    "业主",
    "设计师",
    "橡树湾",
    "风华",
    "工地",
]


def main() -> int:
    failures: list[str] = []
    for directory in SCAN_DIRS:
        for path in directory.rglob("*"):
            if path.suffix not in {".py", ".md", ".toml", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN:
                if marker in text:
                    failures.append(f"{path.relative_to(ROOT)} contains forbidden marker {marker!r}")
    if failures:
        print("\n".join(failures))
        return 1
    print("FastAction boundary validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
