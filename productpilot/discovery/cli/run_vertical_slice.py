"""CLI entrypoint for the vertical slice."""

from __future__ import annotations

import argparse
from pathlib import Path

from productpilot.discovery.service import DiscoveryEngineService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Myntra wishlist discovery vertical slice")
    parser.add_argument("command", choices=["ingest", "classify", "aggregate", "run-all", "ask"])
    parser.add_argument("--question", help="Question for ask command")
    args = parser.parse_args()

    service = DiscoveryEngineService(Path(__file__).resolve().parents[3])

    if args.command == "ingest":
        print(service.ingest())
    elif args.command == "classify":
        print({"classified": service.classify()})
    elif args.command == "aggregate":
        print(service.aggregate())
    elif args.command == "run-all":
        print(service.ingest())
        print({"classified": service.classify()})
        print(service.aggregate())
    elif args.command == "ask":
        if not args.question:
            raise SystemExit("--question is required for ask")
        print(service.answer(args.question))


if __name__ == "__main__":
    main()
