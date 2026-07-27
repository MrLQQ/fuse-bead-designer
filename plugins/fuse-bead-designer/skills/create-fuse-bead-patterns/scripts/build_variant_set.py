"""Validate compiled semantic variants and build their comparison artifacts."""

import argparse
import json
from pathlib import Path
import sys


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from fuse_bead_designer.variant_set import (
    render_variant_comparison,
    validate_variant_set,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants-root", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--comparison", required=True)
    arguments = parser.parse_args(argv)

    summary = validate_variant_set(arguments.variants_root)
    summary_path = Path(arguments.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_variant_comparison(summary, arguments.comparison)
    print(
        f"validated {len(summary['variants'])} variants; "
        f"recommended={summary['recommended']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
