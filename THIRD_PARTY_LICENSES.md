# Third-Party License Notes

This repository publishes wheelhouse artifacts for optional AV ImgData features. The release assets are binary redistribution artifacts from upstream Python packages plus one locally built `insightface` wheel for DSM-compatible Python 3.8 environments.

## Important Scope

- This repository publishes Python package wheels and a manifest.
- This repository does **not** publish InsightFace pretrained models.
- AV ImgData must not auto-bundle or redistribute InsightFace model packs through this repository.

## Key Packages

- `insightface==0.7.3`: MIT for the Python library code.
- `onnxruntime==1.16.3`: MIT.
- `opencv-python-headless==4.10.0.84`: OpenCV is Apache 2.0; the wheel also includes third-party components and notices.

## Important Redistribution Notes

- InsightFace upstream states that pretrained models are available only for non-commercial research purposes. That restriction applies to models, not to the Python library code itself.
- `opencv-python-headless` ships third-party notices and includes FFmpeg under LGPLv2.1 according to the upstream PyPI package documentation.
- Additional wheels in the release set include further licenses such as MPL-2.0, BSD variants, LGPL-3.0 and mixed/dual-licensed packages.

## Practical Publication Rule

Before publishing a new release, verify at minimum:

- the release contains all upstream license files shipped inside the wheels,
- no InsightFace model files are included,
- the wheelhouse manifest matches the actual release assets,
- no locally built wheel contains private paths, secrets or personal data beyond intended package metadata.
