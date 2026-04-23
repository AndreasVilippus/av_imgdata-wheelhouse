# AV ImgData Wheelhouse

Build and publish optional Python wheels for AV ImgData on DSM-compatible targets.

This repository is intended to produce release assets, not to store binary wheels in Git history. Wheels should be uploaded to GitHub Releases together with a manifest that AV ImgData can download, verify, and install from a local cache.

## Targets

Initial target:

- `dsm7-x86_64-python38`

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
  onnxruntime-1.19.2-cp38-cp38-manylinux_2_27_x86_64.whl
```

AV ImgData should consume the manifest, download only the matching files, verify SHA256 hashes, then install with:

```bash
pip install --no-index --find-links <local-wheelhouse> -r requirements-optional-insightface.txt
```

## Build

Run builds inside the DSM-compatible chroot used by the Synology toolkit. Avoid building native wheels on a modern generic Linux host unless the output is audited for DSM compatibility.

```bash
./build/build-insightface.sh dsm7-x86_64-python38
```

The script writes wheels to `wheelhouse/<target>/` and generates `wheelhouse/<target>/wheelhouse-manifest.json`.

