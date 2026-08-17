# Security Policy

## Supported versions

Only the latest release on `main` is supported.

## Reporting a vulnerability

Please report security issues privately through GitHub:

1. Open the repository Security tab.
2. Use “Report a vulnerability.”

Do not open a public issue for a suspected vulnerability.

## Credential expectations

The CLI stores only a Firebase refresh token in an owner-only local session file. It does not store account passwords, Firebase ID tokens, browser cookies, or private saved-job data on disk.

Valid security reports include:

- unauthorized credential exposure caused by this CLI
- unsafe local file or cache permissions
- credential leakage in output, logs, tests, or error paths
- unsafe handling of untrusted API data

Not valid:

- disclosure of the public Firebase web API key already present in the site’s public client bundle
- committed refresh tokens, ID tokens, cookies, passwords, real UIDs, emails, or private saved-job data you added yourself
- abuse of Hiring Cafe infrastructure, rate limits, or accounts
- issues in Hiring Cafe or Firebase that are outside this client
