# Publishing Cerebrain to PyPI and uv

## Prerequisites

- Python 3.11+
- [build](https://pypi.org/project/build/) (for building wheels/sdist)
- [twine](https://pypi.org/project/twine/) (for uploading to PyPI)
- PyPI account and API token ([pypi.org](https://pypi.org))

Optional: [uv](https://docs.astral.sh/uv/) for fast builds and publish.

## 1. Bump version

Edit `pyproject.toml` and `cerebrain/__init__.py`: set `version` and
`__version__` to the new release (e.g. `0.3.4`).

## 2. Build

From the repo root (where `pyproject.toml` lives):

```bash
# With pip + build
pip install build
python -m build
```

Or with uv:

```bash
uv build
```

This produces `dist/cerebrain-<version>.tar.gz` (sdist) and
`dist/cerebrain-<version>-py3-none-any.whl` (wheel). The PyPI package name is
`cerebrain`.

## 3. Check the package (optional)

```bash
pip install twine
twine check dist/*
```

**Production PyPI:**

```bash
twine upload dist/*
# Use __token__ as username and your PyPI API token as password.
```

Or with uv:

```bash
uv publish
# Uses UV_PUBLISH_TOKEN or prompts for token.
```

## 5. uv registry

`uv tool install cerebrain` and `uv pip install cerebrain` use PyPI by default.
Once the package is on PyPI, it is automatically available to uv. No separate
“uv repo” step. The CLI command is `cerebrain`.

## 6. After release

- Tag the release: `git tag v0.3.4 && git push origin v0.3.4`
- Create a GitHub Release and attach the same version notes.
- Optionally add a `CHANGELOG.md` and link it from the release.

## Checklist

- [ ] Version bumped in `pyproject.toml` and `cerebrain/__init__.py`
- [ ] `python -m build` or `uv build` runs without errors
- [ ] `twine check dist/*` passes
- [ ] Test install from Test PyPI
- [ ] Upload to PyPI
- [ ] `pip install cerebrain` and `uv tool install cerebrain` work; run
      `cerebrain --help`
- [ ] Git tag and GitHub release created
