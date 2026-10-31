#!/usr/bin/env python3
"""Scan macOS listening TCP ports and surface identifying detail for each.

Prints a single JSON object to stdout:
  {"scope": "dev-ports" | "all", "ports_scanned": [...] | None, "results": [...]}

Each result: port, protocol, pid, process, app (resolved .app bundle name or
None), command (full path + args), ppid, started (wall-clock), elapsed.
"""

import json
import subprocess
import sys

DEV_PORTS = [
    3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010,
    4000, 4200,
    5000, 5001, 5173, 5174, 5432, 5555, 5672,
    6379, 6380,
    7000,
    8000, 8001, 8080, 8081, 8082, 8888,
    9000, 9090, 9200, 9229,
    11434, 11435,
    15672, 27017,
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def resolve_app_name(command):
    marker = ".app/Contents/MacOS/"
    idx = command.find(marker)
    if idx == -1:
        return None
    before = command[:idx]
    app_start = before.rfind("/")
    return before[app_start + 1 :] if app_start != -1 else before


def main():
    widen = "--all" in sys.argv

    lsof_out = run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"])
    lines = lsof_out.strip().splitlines()[1:]  # skip header row

    seen = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 9:
            continue
        process, pid = parts[0], parts[1]
        name_field = parts[-2] if parts[-1] == "(LISTEN)" else parts[-1]
        if ":" not in name_field:
            continue
        port_str = name_field.rsplit(":", 1)[-1]
        if not port_str.isdigit():
            continue
        port = int(port_str)

        if not widen and port not in DEV_PORTS:
            continue

        seen[(port, pid)] = process

    results = []
    for (port, pid), process in sorted(seen.items()):
        ps_out = run(
            ["ps", "-p", pid, "-o", "lstart=,etime=,ppid=,command="]
        ).strip()
        if not ps_out:
            continue  # process exited between the two lookups

        tokens = ps_out.split()
        started = " ".join(tokens[0:5])  # weekday month day time year
        etime = tokens[5]
        ppid = tokens[6]
        command = " ".join(tokens[7:])

        results.append(
            {
                "port": port,
                "protocol": "TCP",
                "pid": int(pid),
                "process": process,
                "app": resolve_app_name(command),
                "command": command,
                "ppid": int(ppid),
                "started": started,
                "elapsed": etime,
            }
        )

    print(
        json.dumps(
            {
                "scope": "all" if widen else "dev-ports",
                "ports_scanned": None if widen else DEV_PORTS,
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
