"""Send a bounded operational event to the configured private email-delivery webhook."""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

_RECIPIENT = "xnegis@gmail.com"
_SUMMARY = re.compile(r"^[A-Za-z0-9 .:_/@-]{1,240}$")
_EVENTS = {"deploy-failed", "readiness-failed", "storage-failed", "cleanup-failed"}


def _webhook_from_env_file(path: str) -> str:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit("operator alert environment file is unavailable") from exc
    values = [
        line.split("=", 1)[1].strip()
        for line in lines
        if line.strip().startswith("OPERATOR_ALERT_WEBHOOK_URL=")
    ]
    if len(values) != 1:
        raise SystemExit("operator alert environment file must define one webhook URL")
    return values[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", choices=sorted(_EVENTS), required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--env-file")
    args = parser.parse_args()
    if _SUMMARY.fullmatch(args.summary) is None:
        raise SystemExit("summary contains unsupported characters or length")
    endpoint = os.getenv("OPERATOR_ALERT_WEBHOOK_URL", "").strip()
    if not endpoint and args.env_file:
        endpoint = _webhook_from_env_file(args.env_file)
    if not endpoint.startswith("https://"):
        raise SystemExit("OPERATOR_ALERT_WEBHOOK_URL must be an HTTPS URL")
    payload = json.dumps(
        {"recipient": _RECIPIENT, "event": args.event, "summary": args.summary}
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise SystemExit("operator alert delivery failed")
    except Exception as exc:
        raise SystemExit("operator alert delivery failed") from exc


if __name__ == "__main__":
    main()
