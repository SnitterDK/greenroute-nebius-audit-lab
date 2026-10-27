#!/usr/bin/env python3
"""Run one auditable Token Factory request and save a secret-free receipt."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from nebius_audit import audit_decision

DEFAULT_MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="sample-decision.json")
    parser.add_argument("--output", default="evidence/live-receipt.json")
    parser.add_argument("--model", default=os.environ.get("NEBIUS_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        raise SystemExit("NEBIUS_API_KEY is missing; create it in Token Factory and keep it out of files")
    decision = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = audit_decision(decision, args.model, api_key, allow_live=True)
    receipt = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "provider": "Nebius Token Factory", **result}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
