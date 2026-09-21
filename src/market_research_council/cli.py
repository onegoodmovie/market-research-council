"""Command-line interface for the public demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .orchestrator import ResearchCouncil


def render_markdown(report: dict) -> str:
    lines = [
        f"# Council Report for {report['symbol']}",
        "",
        f"**As of:** {report['as_of']}",
        f"**Regime:** {report['regime']}",
        f"**Conviction:** {report['conviction']}",
        "",
        report["summary"],
        "",
        "## Independent evidence",
    ]
    for item in report["evidence"]:
        lines.append(f"- **{item['agent']}** [{item['direction']}, {item['confidence']}]: {item['claim']}")
        for limitation in item["limitations"]:
            lines.append(f"  - Limitation: {limitation}")

    lines.extend(["", "## Audit"])
    for item in report["audit"]:
        lines.append(f"- **{item['severity']}**: {item['message']}")

    lines.extend(["", "## Scenarios"])
    for item in report["scenarios"]:
        lines.extend(
            [
                f"### {item['name']} ({item['probability']}%)",
                f"- Trigger: {item['trigger']}",
                f"- Invalidation: {item['invalidation']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Market Research Council on a JSON snapshot.")
    parser.add_argument("snapshot", type=Path, help="Path to a market snapshot JSON file")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Optional output file")
    args = parser.parse_args(argv)

    with args.snapshot.open(encoding="utf-8") as stream:
        snapshot = json.load(stream)

    report = ResearchCouncil().run(snapshot).to_dict()
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else render_markdown(report)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
