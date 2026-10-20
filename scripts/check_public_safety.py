#!/usr/bin/env python3
"""Reject production inventory and obvious credential material from this repo."""
from __future__ import annotations

import re
import subprocess
import sys

PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
CREDENTIAL_VALUE = re.compile(
    r"(?i)\b(?:password|token|secret|api[_-]?key)\b\s*[:=]\s*"
    r"(?!\{\{|\$\{|REPLACE_ME|CHANGEME|<[^>]+>)[^\s#][^\n#]*"
)


def main() -> int:
    paths = subprocess.check_output(["git", "ls-files", "-z"], text=False).split(b"\0")
    findings: list[str] = []
    for raw_path in paths:
        if not raw_path:
            continue
        path = raw_path.decode()
        if path.startswith("inventories/production/"):
            findings.append(f"{path}: production inventory must remain in Semaphore")
            continue
        with open(path, encoding="utf-8", errors="replace") as source:
            for line_number, line in enumerate(source, start=1):
                if PRIVATE_KEY.search(line):
                    findings.append(f"{path}:{line_number}: private key material")
                if CREDENTIAL_VALUE.search(line):
                    findings.append(f"{path}:{line_number}: possible credential value")
    if findings:
        print("Public-safety check failed:", *findings, sep="\n  ")
        return 1
    print("Public-safety check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
