#!/bin/sh
set -eu

TARGET="${1:-dsm7-x86_64-python38}"
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
RUNTIME_REQS="${ROOT_DIR}/build/requirements-runtime-insightface.txt"
WHEEL_DIR="${ROOT_DIR}/wheelhouse/${TARGET}"
VENV_DIR="${ROOT_DIR}/.venv/test-${TARGET}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d "${WHEEL_DIR}" ]; then
    echo "wheelhouse target not found: ${WHEEL_DIR}" >&2
    exit 1
fi

rm -rf "${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"

PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

export NO_ALBUMENTATIONS_UPDATE=1

"${PYTHON}" -m pip install --upgrade pip setuptools wheel
"${PIP}" install --no-index --find-links "${WHEEL_DIR}" -r "${RUNTIME_REQS}"

"${PYTHON}" - <<'PY'
import cv2
import onnxruntime
from insightface.app import FaceAnalysis
import insightface

print("cv2", cv2.__version__)
print("onnxruntime", onnxruntime.__version__)
print("insightface", getattr(insightface, "__version__", "unknown"))
print("FaceAnalysis", FaceAnalysis)
PY
