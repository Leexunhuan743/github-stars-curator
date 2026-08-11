#!/usr/bin/env python3
"""Initialize the workspace taxonomy from the bundled template.

Copies references/taxonomy-template.yaml to <workspace>/taxonomy.yaml and
verifies the copy parses. Refuses to overwrite an existing workspace
taxonomy.

Usage:

    python scripts/init_taxonomy.py --out-dir "<workspace>"
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import apply_user_lists as sync

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "taxonomy-template.yaml"


def main():
    parser = argparse.ArgumentParser(
        description="Initialize <workspace>/taxonomy.yaml from the bundled template."
    )
    parser.add_argument("--out-dir", required=True, help="Workspace directory")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Template YAML; defaults to the bundled taxonomy-template.yaml")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    template = Path(args.template).resolve()
    if not template.exists():
        raise ValueError(f"Template not found: {template}")
    target = out_dir / "taxonomy.yaml"
    if target.exists():
        print(f"{target} already exists; leaving it untouched (it may be customized).")
        print(f"Current: {len(sync.load_taxonomy(target)['names'])} lists.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, target)
    taxonomy = sync.load_taxonomy(target)
    print(f"Initialized: {target}")
    print(f"Copied {len(taxonomy['names'])} lists from {template.name}.")
    print("Edit taxonomy.yaml to add or rename lists, then reclassify affected repos.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
