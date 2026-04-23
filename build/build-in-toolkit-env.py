#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_TARGET = "dsm7-x86_64-python38"
DEFAULT_PYTHON = "/bin/python3.8"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def toolkit_root(root: Path) -> Path:
    source_dir = root.parent
    toolkit = source_dir.parent
    if source_dir.name != "source":
        raise SystemExit(f"expected repository below a toolkit source/ directory, got: {root}")
    if not (toolkit / "pkgscripts-ng").is_dir():
        raise SystemExit(f"pkgscripts-ng not found next to source/: {toolkit / 'pkgscripts-ng'}")
    if not (toolkit / "build_env").is_dir():
        raise SystemExit(f"build_env not found next to source/: {toolkit / 'build_env'}")
    return toolkit


def available_chroots(build_env: Path):
    pattern = re.compile(r"^ds\.(?P<platform>.+)-(?P<version>[0-9.]+)$")
    result = []
    for path in sorted(build_env.iterdir()):
        if not path.is_dir():
            continue
        match = pattern.match(path.name)
        if match:
            result.append((match.group("platform"), match.group("version"), path))
    return result


def select_chroot(build_env: Path, platform: str, version: str) -> tuple[str, str, Path]:
    chroots = available_chroots(build_env)
    if not chroots:
        raise SystemExit(f"no ds.<platform>-<version> chroots found in {build_env}")

    candidates = []
    for candidate_platform, candidate_version, path in chroots:
        if platform and candidate_platform != platform:
            continue
        if version and candidate_version != version:
            continue
        candidates.append((candidate_platform, candidate_version, path))

    if not candidates:
        available = ", ".join(f"{item[0]}-{item[1]}" for item in chroots)
        raise SystemExit(f"matching chroot not found. requested platform={platform or '*'} version={version or '*'}; available: {available}")
    if len(candidates) > 1:
        available = ", ".join(f"{item[0]}-{item[1]}" for item in candidates)
        raise SystemExit(f"multiple matching chroots found; specify -p and -v explicitly: {available}")
    return candidates[0]


def import_build_env(toolkit: Path):
    python_include = toolkit / "pkgscripts-ng" / "include" / "python"
    sys.path.insert(0, str(python_include))
    import BuildEnv  # type: ignore
    return BuildEnv


def link_project_with_toolkit(toolkit: Path, project: str, platform: str, version: str) -> None:
    build_env = import_build_env(toolkit)
    build_env.LinkProject(project, platform, version)


def chroot_command() -> str:
    resolved = shutil.which("chroot")
    if resolved:
        return resolved
    for candidate in ("/usr/sbin/chroot", "/usr/bin/chroot", "/sbin/chroot", "/bin/chroot"):
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("chroot command not found")


def run_chroot(chroot: Path, command: list[str], *, dry_run: bool = False) -> None:
    full_command = [chroot_command(), str(chroot)] + command
    print("+ " + " ".join(full_command))
    if dry_run:
        return
    subprocess.check_call(full_command)


def sync_wheelhouse_output(chroot: Path, project: str, target: str, root: Path, *, dry_run: bool = False) -> None:
    source_dir = chroot / "source" / project / "wheelhouse" / target
    target_dir = root / "wheelhouse" / target
    print(f"sync {source_dir} -> {target_dir}")
    if dry_run:
        return
    if not source_dir.is_dir():
        raise SystemExit(f"wheelhouse output not found: {source_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        shutil.copy2(path, target_dir / path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AV ImgData wheels in an existing Synology toolkit chroot.")
    parser.add_argument("-p", "--platform", default="", help="Toolkit platform, e.g. geminilake. Defaults to the single matching chroot.")
    parser.add_argument("-v", "--version", default="", help="DSM toolkit version, e.g. 7.3. Defaults to the single matching chroot.")
    parser.add_argument("-t", "--target", default=DEFAULT_TARGET, help=f"Wheelhouse target name. Default: {DEFAULT_TARGET}")
    parser.add_argument("--python", default=DEFAULT_PYTHON, help=f"Python executable inside chroot. Default: {DEFAULT_PYTHON}")
    parser.add_argument("--info-only", action="store_true", help="Only print target information inside chroot.")
    parser.add_argument("--test", action="store_true", help="Install from the generated wheelhouse into a clean venv inside chroot and run import checks.")
    parser.add_argument("--sync-only", action="store_true", help="Only copy existing wheelhouse output from the selected chroot back to this repository.")
    parser.add_argument("--no-sync", action="store_true", help="Do not copy wheelhouse output back after a successful build.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    args = parser.parse_args()

    root = repo_root()
    toolkit = toolkit_root(root)
    project = root.name
    platform, version, chroot = select_chroot(toolkit / "build_env", args.platform, args.version)

    print(f"toolkit={toolkit}")
    print(f"project={project}")
    print(f"platform={platform}")
    print(f"version={version}")
    print(f"chroot={chroot}")
    print(f"target={args.target}")
    print(f"python={args.python}")

    if args.sync_only:
        sync_wheelhouse_output(chroot, project, args.target, root, dry_run=args.dry_run)
        return

    if not args.dry_run:
        link_project_with_toolkit(toolkit, project, platform, version)

    if args.info_only:
        command = [
            "env",
            f"PYTHON_BIN={args.python}",
            f"/source/{project}/build/print-target-info.sh",
        ]
    elif args.test:
        command = [
            "env",
            f"PYTHON_BIN={args.python}",
            f"/source/{project}/build/test-wheelhouse.sh",
            args.target,
        ]
    else:
        command = [
            "env",
            f"PYTHON_BIN={args.python}",
            f"/source/{project}/build/build-insightface.sh",
            args.target,
        ]
    run_chroot(chroot, command, dry_run=args.dry_run)
    if not args.info_only and not args.test and not args.no_sync:
        sync_wheelhouse_output(chroot, project, args.target, root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
