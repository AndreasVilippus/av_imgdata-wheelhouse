# Wheel Targets

## Initial Target

`dsm7-x86_64-python38`

This is the first supported wheel target for AV ImgData optional InsightFace support.

Known runtime facts from the current NAS/package environment:

- DSM generation: DSM 7
- AV ImgData package minimum DSM version: `7.3-00000`
- CPU architecture: `x86_64`
- Python ABI: `cp38`
- Optional InsightFace runtime package currently runs inside the AV ImgData venv

The target is intentionally more specific than the SPK architecture. AV ImgData itself is currently packaged as `noarch`, but InsightFace wheels are native and must match the runtime ABI and system libraries.

## Confirmation Checklist

Run this inside the DSM-compatible chroot and, if possible, once on the NAS:

```bash
./build/print-target-info.sh
```

Or from a toolkit checkout outside the chroot:

```bash
./build/build-in-toolkit-env.py -v 7.3 -p geminilake --info-only
```

Expected first target:

```text
target=dsm7-x86_64-python38
machine=x86_64
python_tag=cp38
```

Before publishing the first release, confirm:

- `machine` is `x86_64`
- `python_tag` is `cp38`
- `libc` is not newer than the NAS runtime
- the resulting wheels pass import tests in a clean AV ImgData-like venv

## Future Targets

Planned naming convention:

- `dsm7-x86_64-python38`
- `dsm7-aarch64-python38`

Only add a new target after a wheel has been built and import-tested in a matching DSM runtime or chroot.
