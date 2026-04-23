#!/bin/sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"

"${PYTHON_BIN}" - <<'PY'
import json
import os
import platform
import sys
import sysconfig


def python_tag() -> str:
    return f"cp{sys.version_info.major}{sys.version_info.minor}"


def normalize_machine(value: str) -> str:
    machine = (value or "").strip().lower()
    if machine in {"amd64", "x64"}:
        return "x86_64"
    if machine in {"arm64"}:
        return "aarch64"
    return machine


machine = normalize_machine(platform.machine())
tag = python_tag()
target = f"dsm7-{machine}-python{sys.version_info.major}{sys.version_info.minor}"

payload = {
    "target": target,
    "machine": machine,
    "python_version": platform.python_version(),
    "python_tag": tag,
    "soabi": sysconfig.get_config_var("SOABI") or "",
    "platform": platform.platform(),
    "libc": platform.libc_ver(),
    "executable": sys.executable,
    "synopkg_pkgdest": os.getenv("SYNOPKG_PKGDEST", ""),
    "synopkg_pkgvar": os.getenv("SYNOPKG_PKGVAR", ""),
}

for key in ("target", "machine", "python_version", "python_tag", "soabi", "platform", "libc", "executable"):
    print(f"{key}={payload[key]}")
print("json=" + json.dumps(payload, sort_keys=True))
PY

