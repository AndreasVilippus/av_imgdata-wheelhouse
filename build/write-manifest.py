#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


WHEEL_RE = re.compile(
    r"^(?P<namever>.+?)-(?P<version>[0-9][^-]*)-(?P<py>[^-]+)-(?P<abi>[^-]+)-(?P<platform>[^.]+(?:\.[^.]+)*)\.whl$"
)


def normalized_name(value: str) -> str:
    return value.replace("_", "-").lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_name_from_wheel(filename: str) -> str:
    match = WHEEL_RE.match(filename)
    if not match:
        return filename
    namever = match.group("namever")
    version = match.group("version")
    suffix = f"-{version}"
    if namever.endswith(suffix):
        return normalized_name(namever[: -len(suffix)])
    return normalized_name(namever)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--wheel-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    wheel_dir = Path(args.wheel_dir)
    wheels = sorted(wheel_dir.glob("*.whl"))
    packages = []
    for wheel in wheels:
        packages.append({
            "name": package_name_from_wheel(wheel.name),
            "file": wheel.name,
            "sha256": sha256(wheel),
            "size": wheel.stat().st_size,
        })

    manifest = {
        "schema_version": 1,
        "target": args.target,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requirements_file": Path(args.requirements).name,
        "packages": packages,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

