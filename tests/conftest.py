from pathlib import Path
import sys


SCRIPT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "fuse-bead-designer"
    / "skills"
    / "create-fuse-bead-patterns"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_ROOT))
