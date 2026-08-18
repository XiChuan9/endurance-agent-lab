#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from endurance_agent_lab.analytics import derive_metrics
from endurance_agent_lab.io import load_model
from endurance_agent_lab.models.context import AthleteContext


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("context")
    args = parser.parse_args()
    context = load_model(args.context, AthleteContext)
    print(json.dumps(derive_metrics(context).model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
