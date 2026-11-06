#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nubian Ibex and IbexWall contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Validates the IbexWall compliance profiles.

Enforces the schema shape, that every reference has an https URL and a
consultation date no older than 12 months, and that every automated
check id exists in known-checks.json. Run from the repository root:

    python3 scripts/validate.py

Exits non-zero on the first error and prints every problem it finds.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"
KNOWN_CHECKS = ROOT / "known-checks.json"

CONTROL_ID = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*$")
CHECK_ID = re.compile(r"^[a-z][a-z0-9_.-]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_REFERENCE_AGE_DAYS = 365

errors: list[str] = []


def err(message: str) -> None:
    errors.append(message)
    print(f"error: {message}", file=sys.stderr)


def require(condition: bool, message: str) -> None:
    if not condition:
        err(message)


def valid_date(text: str) -> bool:
    if not DATE.match(text):
        return False
    try:
        datetime.date.fromisoformat(text)
        return True
    except ValueError:
        return False


def reference_ok(ref: dict, where: str) -> None:
    require(isinstance(ref, dict), f"{where}: a reference must be a mapping")
    if not isinstance(ref, dict):
        return
    for field in ("id", "url", "date"):
        require(field in ref and isinstance(ref[field], str) and ref[field], f"{where}: reference missing `{field}`")
    if not isinstance(ref.get("url"), str) or not ref["url"].startswith("https://"):
        err(f"{where}: reference url must be https")
    if isinstance(ref.get("date"), str):
        if not valid_date(ref["date"]):
            err(f"{where}: reference date `{ref['date']}` is not YYYY-MM-DD")
        else:
            try:
                consulted = datetime.date.fromisoformat(ref["date"])
            except ValueError:
                consulted = None
            if consulted and (datetime.date.today() - consulted).days > MAX_REFERENCE_AGE_DAYS:
                err(f"{where}: reference date `{ref['date']}` is older than 12 months")


def control_ok(control: dict, where: str, known: set[str]) -> None:
    require(isinstance(control, dict), f"{where}: a control must be a mapping")
    if not isinstance(control, dict):
        return
    require("control_id" in control, f"{where}: missing control_id")
    cid = control.get("control_id")
    if not isinstance(cid, str) or not CONTROL_ID.match(cid):
        err(f"{where}: control_id `{cid}` is not `<category>.<name>` with lowercase [a-z0-9-] segments")
    require("title" in control and isinstance(control.get("title"), str) and control["title"], f"{where}: missing title")
    kind = control.get("kind")
    require(kind in ("automated", "attestation"), f"{where}: kind must be automated or attestation")

    checks = control.get("checks", [])
    if kind == "automated":
        require(isinstance(checks, list) and len(checks) > 0, f"{where}: an automated control needs at least one check")
        for check in checks:
            if not isinstance(check, str) or not CHECK_ID.match(check):
                err(f"{where}: check `{check}` is not a check id")
            elif check not in known:
                err(f"{where}: check id `{check}` does not exist in known-checks.json")
    else:
        require(not checks, f"{where}: an attestation control must not list checks")

    for index, ref in enumerate(control.get("references", [])):
        reference_ok(ref, f"{where}.references[{index}]")


def main() -> int:
    if not PROFILES_DIR.is_dir():
        err(f"profiles directory not found at {PROFILES_DIR}")
        return 1

    known = json.loads(KNOWN_CHECKS.read_text())["checks"]
    known_ids = set(known)

    profiles = sorted(PROFILES_DIR.glob("*.yaml"))
    if not profiles:
        err(f"no profiles found under {PROFILES_DIR}")
        return 1

    for profile in profiles:
        try:
            data = yaml.safe_load(profile.read_text())
        except yaml.YAMLError as exc:
            err(f"{profile.name}: not valid YAML: {exc}")
            continue
        require(isinstance(data, dict), f"{profile.name}: the document must be a mapping")
        if not isinstance(data, dict):
            continue
        require(isinstance(data.get("framework"), str) and data["framework"], f"{profile.name}: missing framework")
        require(isinstance(data.get("version"), str) and data["version"], f"{profile.name}: missing version")
        controls = data.get("controls")
        require(isinstance(controls, list) and len(controls) > 0, f"{profile.name}: needs at least one control")
        if isinstance(controls, list):
            for index, control in enumerate(controls):
                control_ok(control, f"{profile.name}.controls[{index}]", known_ids)

    if errors:
        print(f"{len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"ok: {len(profiles)} profile(s), {len(known_ids)} known check id(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
