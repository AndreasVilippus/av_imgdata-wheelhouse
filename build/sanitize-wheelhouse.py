#!/usr/bin/env python3
import argparse
import base64
import csv
import hashlib
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version


INSIGHTFACE_CPP = Path("insightface/thirdparty/face3d/mesh/cython/mesh_core_cython.cpp")
INSIGHTFACE_SO = Path("insightface/thirdparty/face3d/mesh/cython/mesh_core_cython.cpython-38-x86_64-linux-gnu.so")
AV_IMGDATA_STATUS = Path("insightface/av_imgdata_status.py")
AV_IMGDATA_STATUS_SOURCE = '"""AV ImgData optional package status provider for InsightFace."""\n\n\ndef _as_non_negative_int(value):\n    try:\n        return max(0, int(value or 0))\n    except (TypeError, ValueError):\n        return 0\n\n\ndef status_blocks(context):\n    """Return package-owned status rows for AV ImgData.\n\n    AV ImgData supplies runtime context, but the optional package decides which\n    status rows are exposed in the package status area.\n    """\n    return [\n        {\n            "key": "generated_face_profiles",\n            "label_key": "status:pip_generated_face_profiles",\n            "fallback_label": "Generated face profiles",\n            "value": _as_non_negative_int((context or {}).get("generated_face_profiles_count")),\n        }\n    ]\n'


def parse_requirements(path: Path):
    requirements = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "--")):
            continue
        req = Requirement(line)
        requirements[canonicalize_name(req.name)] = req
    return requirements


def wheel_info(path: Path):
    name, version, _build, _tags = parse_wheel_filename(path.name)
    return canonicalize_name(name), Version(str(version))


def drop_duplicate_wheels(wheel_dir: Path, requirements_path: Path):
    requirements = parse_requirements(requirements_path)
    by_name = {}
    for wheel in sorted(wheel_dir.glob('*.whl')):
        name, version = wheel_info(wheel)
        by_name.setdefault(name, []).append((version, wheel))

    removed = []
    for name, entries in by_name.items():
        if len(entries) <= 1:
            continue
        req = requirements.get(name)
        satisfying = []
        for version, wheel in entries:
            if req is None or req.specifier.contains(str(version), prereleases=True):
                satisfying.append((version, wheel))
        if not satisfying:
            raise RuntimeError(f'No wheel for {name} satisfies {req}')
        keep_version, keep_wheel = max(satisfying, key=lambda item: item[0])
        for version, wheel in entries:
            if wheel == keep_wheel:
                continue
            wheel.unlink()
            removed.append((name, str(version), wheel.name, keep_wheel.name, str(keep_version)))
    return removed


def record_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    return 'sha256=' + base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')


def rewrite_wheel_from_directory(source_dir: Path, wheel_path: Path) -> None:
    record_rel = next(Path(name) for name in [p.as_posix() for p in source_dir.rglob('RECORD')] if '.dist-info/' in name)
    record_path = source_dir / record_rel
    rows = []
    for file_path in sorted(p for p in source_dir.rglob('*') if p.is_file()):
        rel = file_path.relative_to(source_dir).as_posix()
        if rel == record_rel.as_posix():
            rows.append((rel, '', ''))
        else:
            rows.append((rel, record_hash(file_path), str(file_path.stat().st_size)))

    with record_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)

    tmp_wheel = wheel_path.with_suffix('.tmp.whl')
    if tmp_wheel.exists():
        tmp_wheel.unlink()
    with zipfile.ZipFile(tmp_wheel, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(p for p in source_dir.rglob('*') if p.is_file()):
            archive.write(file_path, file_path.relative_to(source_dir).as_posix())
    tmp_wheel.replace(wheel_path)


def inject_av_imgdata_status_provider(source_dir: Path) -> bool:
    target = source_dir / AV_IMGDATA_STATUS
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current == AV_IMGDATA_STATUS_SOURCE:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(AV_IMGDATA_STATUS_SOURCE, encoding="utf-8")
    return True


def sanitize_insightface_wheel(wheel_path: Path, strip_binary: Optional[str]) -> bool:
    changed = False
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        with zipfile.ZipFile(wheel_path) as archive:
            archive.extractall(workdir)

        cpp_path = workdir / INSIGHTFACE_CPP
        if cpp_path.exists():
            cpp_path.unlink()
            changed = True

        if inject_av_imgdata_status_provider(workdir):
            changed = True

        so_path = workdir / INSIGHTFACE_SO
        if strip_binary and so_path.exists():
            subprocess.check_call([strip_binary, '--strip-debug', str(so_path)])
            changed = True

        if changed:
            rewrite_wheel_from_directory(workdir, wheel_path)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wheel-dir', required=True)
    parser.add_argument('--requirements', required=True)
    parser.add_argument('--strip-binary', default='strip')
    args = parser.parse_args()

    wheel_dir = Path(args.wheel_dir)
    requirements_path = Path(args.requirements)
    strip_binary = shutil.which(args.strip_binary) if args.strip_binary else None

    removed = drop_duplicate_wheels(wheel_dir, requirements_path)
    for name, version, removed_file, kept_file, kept_version in removed:
        print(f'removed duplicate wheel for {name}: {removed_file} ({version}), kept {kept_file} ({kept_version})')

    insightface_wheels = sorted(wheel_dir.glob('insightface-*.whl'))
    for wheel in insightface_wheels:
        if sanitize_insightface_wheel(wheel, strip_binary):
            print(f'sanitized {wheel.name}')


if __name__ == '__main__':
    main()
