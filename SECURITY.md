# Security

## Reporting a vulnerability
Please report security issues privately to **rudraneel93@gmail.com** with "Krama security" in the
subject. Do not open a public issue. We aim to reply within 3 working days.

## How the hosted service protects your data
- Submitted values are processed in memory and never stored or logged; every response carries a SHA-256
  fingerprint of your input for your own audit trail.
- API keys are stored only as hashes, shown once, and can be revoked from the dashboard (effective within
  30 seconds).
- Rules are executed by a whitelisted parser; nothing you send is ever evaluated as code.
- Requests are size-limited, rate-limited and time-limited, with load shedding under pressure.
- The service is scanned with OWASP ZAP, Semgrep, Bandit, Trivy and gitleaks, and fuzzed with
  property-based API tests; every finding has been fixed.

## Scope of this repository
The client, CLI, Excel add-in and docs here are open source. If you find an issue in them, the same
private reporting address applies.
