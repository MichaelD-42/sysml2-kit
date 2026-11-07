"""sysml2kit: bridge SysML v2 models into sphinx-needs and render diagrams."""

import argparse
import json
import re
import sys
from pathlib import Path

from .gaps import gaps
from .needs import BridgeError, text_findings, write_needs
from .render import trace_svg, use_case_svg, use_cases


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sysml2kit", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "needs", help="interchange JSON (`sysml export`) -> sphinx-needs needs.json"
    )
    p.add_argument("export")
    p.add_argument("output")
    p.add_argument(
        "model_files", nargs="+", help="the .sysml files, for source locations"
    )
    p = sub.add_parser("usecases", help="one use case diagram SVG per subject")
    p.add_argument("export")
    p.add_argument("output_dir")
    p = sub.add_parser(
        "trace",
        help="RFLP trace graph SVG from a sphinx-needs needs.json (`sphinx-build -b needs`)",
    )
    p.add_argument("needs_json")
    p.add_argument("output")
    p = sub.add_parser(
        "gaps",
        help="RFLP rule violations by layer, from a `sphinx-build -b needs` output directory",
    )
    p.add_argument("needs_dir", help="holds needs.json and schema_violations.json")
    p.add_argument(
        "--layer",
        choices="RFLV",
        help="only rules gating this layer or an earlier one",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "needs":
            needs = write_needs(args.export, args.output, args.model_files)
            print(f"sysml2kit: {len(needs)} needs -> {args.output}")
            for finding in text_findings(needs):
                print(f"sysml2kit: warning: {finding}", file=sys.stderr)
        elif args.command == "usecases":
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            for subject, cases in use_cases(json.loads(Path(args.export).read_text())):
                path = out / f"usecases-{re.sub(r'[^A-Za-z0-9_-]', '_', subject)}.svg"
                path.write_text(use_case_svg(subject, cases))
                print(f"sysml2kit: {len(cases)} use cases -> {path}")
        elif args.command == "trace":
            data = json.loads(Path(args.needs_json).read_text())
            needs = data["versions"][data.get("current_version", "")]["needs"]
            Path(args.output).write_text(trace_svg(needs))
            print(f"sysml2kit: trace of {len(needs)} needs -> {args.output}")
        elif args.command == "gaps":
            out = Path(args.needs_dir)
            data = json.loads((out / "needs.json").read_text())
            needs = data["versions"][data.get("current_version", "")]["needs"]
            violations = json.loads((out / "schema_violations.json").read_text())
            found = gaps(violations, needs, args.layer)
            for layer, rule, need_id, where, message in found:
                print(f"{layer}  {rule}  {need_id}  {where}  {message}")
            print(f"sysml2kit: {len(found)} gaps", file=sys.stderr)
            sys.exit(1 if found else 0)
    except BridgeError as err:
        sys.exit(f"sysml2kit: {err}")


if __name__ == "__main__":
    main()
