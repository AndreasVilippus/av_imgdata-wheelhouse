# AV ImgData Wheelhouse

Build and publish optional Python wheels for AV ImgData on DSM-compatible targets.

This repository is intended to produce release assets, not to store binary wheels in Git history. Wheels should be uploaded to GitHub Releases together with a manifest that AV ImgData can download, verify, and install from a local cache.

## Targets

Initial target:

- `dsm7-x86_64-python38`

See `TARGETS.md` for target naming and confirmation steps.

Planned target naming:

- `dsm7-x86_64-python38`
- `dsm7-aarch64-python38`

The target must match the NAS runtime closely enough for native wheels:

- CPU architecture
- Python ABI
- glibc/system library compatibility
- DSM runtime library set

## Release Layout

Use one GitHub release per target and build date or package set:

```text
dsm7-x86_64-python38-2026.04.23
  wheelhouse-manifest.json
  insightface-0.7.3-cp38-cp38-linux_x86_64.whl
  opencv_python_headless-4.10.0.84-cp37-abi3-linux_x86_64.whl
  onnxruntime-1.16.3-cp38-cp38-manylinux_2_17_x86_64.whl
```

AV ImgData should consume the manifest, download only the matching files, verify SHA256 hashes, then install with:

```bash
pip install --no-index --find-links <local-wheelhouse> -r requirements-optional-insightface.txt
```

## Build

Run builds inside the DSM-compatible chroot used by the Synology toolkit. Avoid building native wheels on a modern generic Linux host unless the output is audited for DSM compatibility.

From a standard toolkit checkout with this repository below `source/`:

```bash
cd /path/to/toolkit/source/av_imgdata-wheelhouse
./build/build-in-toolkit-env.py -v 7.3 -p geminilake
```

Run this from a shell that is allowed to use the toolkit chroot, equivalent to the shell used for:

```bash
cd /path/to/toolkit/pkgscripts-ng
./PkgCreate.py -v 7.3 -c av_imgdata
```

The wrapper works relative to the repository location:

- detects the toolkit root from `../..`
- uses the existing `pkgscripts-ng` and `build_env`
- links the project into the selected chroot under `/source/av_imgdata-wheelhouse`
- runs the wheel build inside the selected chroot with Python 3.8

To only inspect the selected target environment:

```bash
./build/build-in-toolkit-env.py -v 7.3 -p geminilake --info-only
```

The lower-level build script can still be run directly inside the chroot:

```bash
./build/build-insightface.sh dsm7-x86_64-python38
```

The InsightFace source build intentionally runs with `--no-build-isolation` and `cython<3`. The DSM 7.3/geminilake toolchain uses GCC 4.9.2; isolated builds may pull Cython 3.x, which can generate C++ requiring `<string_view>`, unavailable in that compiler.

The script writes wheels to `wheelhouse/<target>/` and generates `wheelhouse/<target>/wheelhouse-manifest.json`.
