#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Actively probes a local workspace and host environment for the 4 Resident Agent pillars."""

import json
import os
import pathlib
import subprocess
import sys


def probe_workspace(root: pathlib.Path) -> dict:
    # 1. Persistent Identity / Daemon supervisor evidence
    daemon_markers = []
    if pathlib.Path("/.dockerenv").exists():
        daemon_markers.append("/.dockerenv")
    for pat in ("Dockerfile", "docker-compose.yml", "compose.yaml", "*.nomad", "*.service", "tools/bridge.py", "bin/*"):
        found = list(root.glob(pat))[:2]
        daemon_markers.extend(str(p.relative_to(root)) for p in found)

    # 2. Durable Memory store evidence
    memory_markers = []
    for pat in ("memory", "data/*.db", "data/*.sqlite*", "**/MEMORY.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        found = list(root.glob(pat))[:3]
        memory_markers.extend(str(p.relative_to(root)) for p in found)

    # 3. Scheduled Sidecars / Cron evidence
    schedule_markers = []
    for pat in ("data/schedule.json", "config/schedule*", "tools/*scheduler*.py", "tools/sidecars.py", "bin/*daily*"):
        found = list(root.glob(pat))[:3]
        schedule_markers.extend(str(p.relative_to(root)) for p in found)
    try:
        cron_res = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=2)
        if cron_res.returncode == 0 and cron_res.stdout.strip():
            schedule_markers.append("user_crontab")
    except Exception:
        pass

    # 4. Multi-Agent Peer Coordination / Handoff evidence
    coord_markers = []
    for pat in ("tools/banana.py", "tools/handoff.py", "specs/*handoff*", ".agents/rules/*crab_cavern*", "**/peer_contracts.md"):
        found = list(root.glob(pat))[:3]
        coord_markers.extend(str(p.relative_to(root)) for p in found)

    pillars = {
        "persistent_identity": {"detected": bool(daemon_markers), "evidence": daemon_markers[:4]},
        "durable_memory": {"detected": bool(memory_markers), "evidence": memory_markers[:4]},
        "scheduled_sidecars": {"detected": bool(schedule_markers), "evidence": schedule_markers[:4]},
        "peer_coordination": {"detected": bool(coord_markers), "evidence": coord_markers[:4]},
    }
    detected_count = sum(1 for v in pillars.values() if v["detected"])
    return {
        "workspace": str(root.resolve()),
        "pillars_detected": f"{detected_count}/4",
        "classification": "resident_agent" if detected_count >= 3 else "partial_or_ephemeral_workspace",
        "pillars": pillars,
    }


def main() -> int:
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
    if not target.exists():
        print(json.dumps({"error": f"Path does not exist: {target}"}), file=sys.stderr)
        return 1
    report = probe_workspace(target)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
