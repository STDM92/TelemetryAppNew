from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_ONEDIR = ROOT / "live_telemetry_sidecar.spec"
SPEC_ONEFILE = ROOT / "live_telemetry_sidecar_onefile.spec"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the live telemetry sidecar executable with PyInstaller.")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Build a single-file executable instead of the default onedir build.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete local build/ and dist/ folders before running PyInstaller.",
    )
    parser.add_argument(
        "--noconfirm",
        action="store_true",
        help="Pass --noconfirm to PyInstaller.",
    )
    return parser.parse_args()


def clean_output_dirs() -> None:
    for path in (BUILD_DIR, DIST_DIR):
        if path.exists():
            print(f"Removing {path}")
            shutil.rmtree(path)


def build(onefile: bool, noconfirm: bool) -> int:
    spec_file = SPEC_ONEFILE if onefile else SPEC_ONEDIR

    if not spec_file.is_file():
        print(f"Spec file not found: {spec_file}", file=sys.stderr)
        return 1

    cmd = [sys.executable, "-m", "PyInstaller", str(spec_file)]

    if noconfirm:
        cmd.append("--noconfirm")

    print("Running:", " ".join(str(part) for part in cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    args = parse_args()

    if args.clean:
        clean_output_dirs()

    return build(onefile=args.onefile, noconfirm=args.noconfirm)


if __name__ == "__main__":
    raise SystemExit(main())
