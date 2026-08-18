#!/usr/bin/env python3
from __future__ import annotations

import argparse

from endurance_agent_lab.io import load_model
from endurance_agent_lab.models.audit import AuditOutput


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit")
    args = parser.parse_args()
    output = load_model(args.audit, AuditOutput)
    print(f"valid AuditOutput: {len(output.claims)} claims")


if __name__ == "__main__":
    main()
