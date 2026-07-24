"""Portable entry point for the Fuse Bead Designer compiler."""

from pathlib import Path
import sys


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from fuse_bead_designer.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
