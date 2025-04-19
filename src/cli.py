"""command-line interface."""
from __future__ import annotations

import argparse
import json
import sys

from .graph import run as run_graph
from .llm import llm_from_env
from .render import render_markdown


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="travel-plan")
    p.add_argument("query", help="natural language trip request")
    p.add_argument("--format", choices=["json", "markdown"], default="markdown")
    p.add_argument("--no-llm", action="store_true", help="run without an LLM (uses fallback parser)")
    args = p.parse_args(argv)

    llm = None if args.no_llm else llm_from_env()
    it = run_graph(args.query, llm=llm)
    if args.format == "json":
        print(json.dumps(it.model_dump(mode="json"), indent=2, default=str))
    else:
        print(render_markdown(it))
    return 0


if __name__ == "__main__":
    sys.exit(main())
