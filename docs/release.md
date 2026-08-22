# Release runbook

## One-time owner setup

1. Create a protected GitHub environment named `pypi`.
2. In that environment, set **Deployment branches and tags** to **Selected branches and tags** and add the pattern `v*`.
3. Register the PyPI trusted publisher for `chen-gdp/hiringcafe-cli` with workflow `release.yaml` and environment `pypi`.

## Release

1. Confirm `main` is green and its working tree is clean.
2. Set the package version in `pyproject.toml` and add the matching `CHANGELOG.md` section.
3. Open, review, test, and merge that release PR.
4. Tag the merged commit with the exact matching `vX.Y.Z` tag and push it.
5. Wait for the `Release` workflow. It validates the tag, builds and verifies artifacts, publishes to PyPI, then attaches the same artifacts and checksum file to the GitHub release.
6. Install from PyPI and run `hiringcafe --version`.

## Failure handling

PyPI versions are immutable. If publication fails before upload completes, fix the workflow and rerun it for the same tag. If the upload completed but a later step failed, do not rebuild or reupload the version; repair only the failed GitHub release step and verify the package already exists on PyPI.

Never delete and reuse a released version tag. A partially released version must be superseded by a new version.
