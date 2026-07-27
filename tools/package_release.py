"""Build reproducible Fuse Bead Designer distribution archives."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = "0.4.0"
PLUGIN = ROOT / "plugins" / "fuse-bead-designer"
SKILL = PLUGIN / "skills" / "create-fuse-bead-patterns"
IGNORED_PARTS = frozenset({"__pycache__", ".DS_Store", "work", ".worktrees"})
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def package(source: Path, destination: Path) -> None:
    """Write *source* below its root name using stable member metadata."""
    files = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.relative_to(source).parts)
    )
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            member = Path(source.name) / path.relative_to(source)
            info = zipfile.ZipInfo(member.as_posix(), date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    DIST.mkdir(exist_ok=True)
    package(PLUGIN, DIST / f"fuse-bead-designer-plugin-v{VERSION}.zip")
    package(SKILL, DIST / f"create-fuse-bead-patterns-skill-v{VERSION}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
