# Changelog

## Unreleased

- Initial unofficial Python CLI for Hiring Cafe job search, job details, authentication, saved-job tracking, anonymous-read caching, retries, and stable agent-oriented JSON output.
- Added tagged PyPI release automation using GitHub Trusted Publishing.

## 0.1.5

- Made `hiringcafe --version` read the installed package metadata so it matches PyPI releases.

## 0.1.4

- Staged release artifacts so PyPI receives only distributions while GitHub retains checksums.

## 0.1.3

- Kept the checksum manifest out of the PyPI upload directory while retaining it in GitHub release artifacts.

## 0.1.2

- First PyPI release.
- Fixed release checksum verification and aligned the workflow filename with PyPI Trusted Publishing.
