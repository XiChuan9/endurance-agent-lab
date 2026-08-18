# Privacy Policy for Repository Data

## Default rule

Real athlete data are private unless there is explicit informed consent for a defined public use. A public code license does not grant permission to disclose athlete data.

## Storage boundary

- `private/` contains real athlete contexts and longitudinal tracks and is Git-ignored.
- `runs/` may contain transformed private data and is also Git-ignored.
- `benchmarks/` contains only synthetic, consented, or irreversibly de-identified cases.
- `examples/` contains synthetic data only.

## De-identification standard

Removing a name is insufficient. Before a real decision structure becomes a public case, review dates, exact performances, locations, rare injuries, race names, device IDs, activity names, free text, and combinations that could enable re-identification. Prefer synthetic reconstruction that preserves the reasoning problem rather than row-level disclosure.

## Secrets

API keys belong in environment variables or a secret manager. They must not appear in context files, generated reports, issues, or commits.

## Incident response

If private data are committed, stop distribution, rotate any exposed secret, remove the data from current and historical Git objects where feasible, notify affected maintainers, document the incident, and reassess consent and retention.
