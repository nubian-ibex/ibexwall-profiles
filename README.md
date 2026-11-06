<!-- SPDX-FileCopyrightText: 2026 Nubian Ibex and IbexWall contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# ibexwall-profiles

Compliance profiles for [IbexWall](https://ibexwall.com): each file maps a
framework's controls to the checks the product already measures, so a
machine can report which technical controls it meets, which it does not,
and which a person has to attest to.

IbexWall does not certify anything. A profile says "compliant with the
mapped technical controls" for the framework version named in the file,
never "certified". Certification comes from an independent audit.

## What a profile is

A YAML file with a `framework`, a `version`, and a list of `controls`.
Each control is either:

- `automated`: decided by the machine from the named `checks` (check ids
  emitted by the IbexWall plugins). A control is compliant only when every
  required check passed recently; a missing or stale check makes it
  not-assessed, never compliant.
- `attestation`: decided by a person, who records a statement, an owner
  and an expiry. Organizational controls live here, because software
  cannot prove a backup is tested or an incident process exists.

The shape is fixed by `schema/profile.schema.json`; `known-checks.json`
lists the check ids a profile may reference.

## Layout

- `profiles/` the profiles, one file per framework.
- `schema/profile.schema.json` the JSON Schema.
- `known-checks.json` the registry of check ids the product emits.
- `scripts/validate.py` the local validator.

## Validating

```sh
python3 scripts/validate.py
```

The check enforces the schema, an https URL and a consultation date no
older than 12 months on every reference, and that every check id exists.
CI runs the same script.

## Frameworks and their limits

The first release ships:

- IbexWall Baseline, our own recommended set.
- Lei 13.709/2018 (LGPD), art. 46 with art. 6 VII and art. 49. The law
  names no technical control, so this mapping is our reading, stated
  plainly.
- Resolução CMN 4.893/2021 as amended by CMN 5.274/2025, art. 3 § 2.
- NIST SP 800-53 Rev. 5 and SP 800-171 Rev. 3, the host subset.
- ISO/IEC 27001:2022, Annex A theme 8, number and title only.

PCI DSS and SOC 2 follow as a second release; CIS needs a licensing
review before any Benchmark text or id is shipped. Licensed texts are
never copied: references cite the clause by number and link the source.

## Changing a profile

A changed profile is a release of this repository, not of the app; the
core loads the profile it is given and evaluates it against the stored
check results. Bump nothing in the app for a profile change.
