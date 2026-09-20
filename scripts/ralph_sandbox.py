"""Run a command inside a fresh reqly/E2B sandbox and print a JSON receipt.

Dependency-free: imports the sibling reqly Python SDK (urllib-based).

    REQLY_API_KEY=dev-only-key python3 scripts/ralph_sandbox.py \
        --command 'python3 -c "print(6*7)"'

    # with a file uploaded first
    python3 scripts/ralph_sandbox.py --upload local.py:/workspace/local.py \
        --command 'python3 /workspace/local.py'

    # keep the sandbox alive for inspection
    python3 scripts/ralph_sandbox.py --command 'uname -a' --keep

Never pass secrets or model weights through the sandbox.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_SDK = Path(__file__).resolve().parents[2] / "reqly" / "sdk" / "python"


def _load_sdk() -> None:
    sdk = os.environ.get("REQLY_SDK_PATH", str(DEFAULT_SDK))
    if not Path(sdk).is_dir():
        raise SystemExit(
            f"reqly SDK not found at {sdk}; set REQLY_SDK_PATH to reqly/sdk/python"
        )
    sys.path.insert(0, sdk)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--cwd", default="/workspace")
    parser.add_argument("--timeout-ms", type=int, default=110_000, help="reqly caps this at 120000")
    parser.add_argument("--upload", action="append", default=[], metavar="LOCAL:REMOTE")
    parser.add_argument("--read", action="append", default=[], metavar="REMOTE")
    parser.add_argument("--keep", action="store_true", help="do not destroy the sandbox")
    parser.add_argument("--api-url", default=os.environ.get("REQLY_API_URL", "http://localhost:3100"))
    parser.add_argument("--api-key", default=os.environ.get("REQLY_API_KEY", "dev-only-key"))
    parser.add_argument("--template", default=os.environ.get("REQLY_TEMPLATE", "python"))
    args = parser.parse_args()

    _load_sdk()
    from reqly import Client  # type: ignore

    client = Client(args.api_url, args.api_key, timeout=max(60, args.timeout_ms // 1000 + 30))
    sandbox = client.create_sandbox(template=args.template)
    receipt: dict = {
        "sandbox_id": sandbox.id,
        "api_url": args.api_url,
        "template": args.template,
        "command": args.command,
        "uploads": [],
        "reads": {},
    }
    try:
        for item in args.upload:
            local, _, remote = item.partition(":")
            if not remote:
                raise SystemExit(f"--upload expects LOCAL:REMOTE, got {item!r}")
            sandbox.write_file(remote, Path(local).read_text())
            receipt["uploads"].append({"local": local, "remote": remote})

        timeout_ms = min(args.timeout_ms, 120_000)
        result = sandbox.exec(args.command, cwd=args.cwd, timeout_ms=timeout_ms)
        receipt.update(
            {
                "exit_code": result.get("exitCode", result.get("exit_code")),
                "status": result.get("status"),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "timed_out": result.get("timedOut", result.get("timed_out", False)),
            }
        )
        for remote in args.read:
            try:
                receipt["reads"][remote] = sandbox.read_file(remote)
            except Exception as error:  # noqa: BLE001
                receipt["reads"][remote] = f"<error: {error}>"
    finally:
        if not args.keep:
            try:
                sandbox.destroy()
                receipt["destroyed"] = True
            except Exception:  # noqa: BLE001
                receipt["destroyed"] = False

    json.dump(receipt, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if receipt.get("exit_code") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
