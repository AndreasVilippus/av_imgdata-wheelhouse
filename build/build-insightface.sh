#!/bin/sh
set -eu

TARGET="${1:-dsm7-x86_64-python38}"
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BUILD_REQS="${ROOT_DIR}/build/requirements-build.txt"
RUNTIME_REQS="${ROOT_DIR}/build/requirements-runtime-insightface.txt"
VENV_DIR="${ROOT_DIR}/.venv/${TARGET}"
WHEEL_DIR="${ROOT_DIR}/wheelhouse/${TARGET}"
MANIFEST_PATH="${WHEEL_DIR}/wheelhouse-manifest.json"

PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "${WHEEL_DIR}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

"${PYTHON}" -m pip install --upgrade -r "${BUILD_REQS}"

"${PIP}" wheel \
    --wheel-dir "${WHEEL_DIR}" \
    --no-binary insightface \
    --no-build-isolation \
    -r "${RUNTIME_REQS}"

"${PYTHON}" "${ROOT_DIR}/build/write-manifest.py" \
    --target "${TARGET}" \
    --requirements "${RUNTIME_REQS}" \
    --wheel-dir "${WHEEL_DIR}" \
    --output "${MANIFEST_PATH}"

echo "Wrote ${MANIFEST_PATH}"
