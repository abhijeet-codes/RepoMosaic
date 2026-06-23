"""Command line interface for RepoMosaic."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .graph_builder import GraphBuilder
from .repo_scanner import RepoScanner
from .skill_map import SkillMap


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RepoMosaic repository graph and skill-map CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a repository graph")
    build.add_argument("--repo", required=True, help="Local path or Git URL")
    build.add_argument("--out", help="Output path ending in .json or .graphml")
    build.add_argument("--ext", nargs="*", default=[".py"], help="Extensions to scan")

    skills = sub.add_parser("skills", help="Build contributor skill map from Git history")
    skills.add_argument("--repo", required=True, help="Local Git repository path")
    return parser.parse_args(argv)


def run(argv: Sequence[str]) -> int:
    args = _parse_args(argv)
    if args.command == "build":
        scanner = RepoScanner(args.repo)
        files = scanner.get_files(args.ext)
        builder = GraphBuilder()
        graph = builder.build(files)
        if args.out:
            out = Path(args.out)
            if out.suffix.lower() == ".graphml":
                builder.save_graphml(str(out))
            else:
                builder.save_json(str(out))
            print(f"Graph written to {out}")
        else:
            print(f"Graph built: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    elif args.command == "skills":
        for author, files in SkillMap(args.repo).compute().items():
            print(author)
            for path, count in sorted(files.items()):
                print(f"  {path}: {count}")
    return 0


def main() -> int:
    import sys

    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
