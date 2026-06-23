"""
cli.py
======

Command line interface for RepoMosaic.  This script allows users to
clone or access a repository, build a call graph, compute a skill map
and optionally save the resulting graph to disk.  Use the ``--help``
option to see available commands and flags.

Example usage::

    python -m repomosaic.cli build --repo https://github.com/python/cpython --out graph.json
    python -m repomosaic.cli skills --repo /path/to/local/repo

The CLI is built using the standard library ``argparse`` module to
avoid third‑party dependencies.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .repo_scanner import RepoScanner
from .graph_builder import GraphBuilder
from .skill_map import SkillMap

# Templates for AI assistant integration.  These are simple static files
# written during ``install --project``.  The templates replicate the
# committed versions in the repository and document how agents should
# invoke RepoMosaic.

SKILL_TEMPLATE = """---
name: repomosaic
version: 0.3.0
description: Build a call graph and contributor skill map from a repository.
author: RepoMosaic Developers
trigger: "/repomosaic"
args: |
  repo: string  # Path or HTTPS URL to the repository
  out: string (optional)  # Output directory for graph and skill map
returns: |
  repomosaic-out/graph.json  # JSON representation of the call/import graph
  repomosaic-out/skill_map.json  # JSON contributor skill map
---

# RepoMosaic Skill

RepoMosaic is a Python package and CLI tool that turns a repository
into a call graph and skill map.  When invoked via `/repomosaic`, it
clones or scans the given repository, builds an AST‑based call/import
graph using NetworkX, analyses the Git history to assign commit‑based
skills to contributors, and writes out the resulting graph and skill
map for the assistant to consult.  It is similar to Graphify but
simpler and focused on Python for now.

## How to use

1. Invoke the skill with `/repomosaic <repo>` where `<repo>` is a local
   path or a remote Git HTTPS URL.  RepoMosaic will build a
   `repomosaic-out/` directory containing `graph.json`,
   `skill_map.json` and a short `REPORT.md`.
2. Once the graph is built, you can ask your assistant high‑level
   questions such as "list all functions in module X" or "which
   contributor worked most on file Y?" — the assistant will inspect
   `graph.json` and `skill_map.json` rather than grepping through raw
   files.

## Safety

RepoMosaic only interacts with Git over HTTPS and performs static
analysis via Python's `ast` module.  It never executes arbitrary code
from the repository.  LLM integration is optional and disabled by
default.
"""

AGENTS_TEMPLATE = """# RepoMosaic agent instructions

RepoMosaic is installed in this repository as an AI coding assistant
skill.  Before searching through files, follow these steps to build
and use the knowledge graph:

1. **Build the graph and skill map.**  From the project root, run:

   ```bash
   python -m repomosaic.cli build --repo . --out repomosaic-out/graph.json
   python -m repomosaic.cli skills --repo . > repomosaic-out/skill_map.json
   ```

   This scans the current repository, constructs a call/import graph
   and exports it as `graph.json`.  It also computes a contributor
   skill map and saves it as `skill_map.json`.

2. **Consult the outputs.**  Use the generated files to guide your
   exploration and planning:

   * `graph.json` lists nodes (functions, classes, modules) and edges
     (calls, imports).  Inspect node attributes to understand
     relationships and dependencies.
   * `skill_map.json` lists each contributor and the files they
     touched, along with commit counts.

3. **Ask RepoMosaic for help.**  When asked to explain a module or
   identify who wrote a piece of code, prefer reading
   `graph.json` and `skill_map.json` instead of scanning raw
   files.  The assistant should reference these structures to answer
   questions more accurately and with fewer tokens.

4. **Do not execute repository code.**  RepoMosaic builds graphs
   statically via AST parsing.  It should not be used to run or test
   arbitrary code.

These instructions apply to any coding agent that reads `AGENTS.md`,
including GitHub Copilot Chat, Code Pilot, Claude Code, OpenAI Codex CLI,
Cursor, Trae and many others.  Agents that support pre‑tool hooks will
also see a notification when a `repomosaic-out` directory exists.  On
platforms like Cursor or Trae, which lack pre‑tool hooks, the contents
of this file serve as the always‑on instructions for graph building and
skill mapping.
"""


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RepoMosaic CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build command
    build_parser = subparsers.add_parser("build", help="Build a call graph from a repository")
    build_parser.add_argument("--repo", required=True, help="Path or Git URL to the repository")
    build_parser.add_argument(
        "--out",
        required=False,
        help="Output file path for the graph (GraphML or JSON based on extension)",
    )
    build_parser.add_argument(
        "--ext",
        nargs="*",
        default=[".py"],
        help="File extensions to include (default: .py)",
    )

    # Skills command
    skills_parser = subparsers.add_parser("skills", help="Compute a skill map for a repository")
    skills_parser.add_argument("--repo", required=True, help="Path to a local Git repository")

    # Install command
    install_parser = subparsers.add_parser(
        "install", help="Install RepoMosaic as an AI coding assistant skill"
    )
    install_parser.add_argument(
        "--project",
        action="store_true",
        help="Write SKILL.md and AGENTS.md into the current project",
    )

    return parser.parse_args(argv)


def run(argv: Sequence[str]) -> int:
    args = _parse_args(argv)
    if args.command == "build":
        scanner = RepoScanner(args.repo)
        repo_path = scanner.ensure_local()
        files = scanner.get_files(args.ext)
        builder = GraphBuilder()
        graph = builder.build(files)
        if args.out:
            out_path = Path(args.out)
            if out_path.suffix.lower() == ".graphml":
                builder.save_graphml(str(out_path))
            else:
                builder.save_json(str(out_path))
            print(f"Graph written to {out_path}")
        else:
            print("Graph built with", len(graph.nodes), "nodes and", len(graph.edges), "edges")
    elif args.command == "skills":
        skill_map = SkillMap(args.repo)
        data = skill_map.compute()
        for author, files in data.items():
            print(author)
            for file_path, count in files.items():
                print(f"  {file_path}: {count}")
    elif args.command == "install":
        # Install RepoMosaic as an AI assistant skill
        # Only project-scoped installs are currently supported.
        if not args.project:
            print(
                "Only project-scoped installs are supported. Use --project to write files to the current repository."
            )
            return 1
        # Determine paths
        root = Path.cwd()
        skill_dir = root / ".claude" / "skills" / "repomosaic"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        agents_path = root / "AGENTS.md"
        # Write files
        skill_path.write_text(SKILL_TEMPLATE)
        agents_path.write_text(AGENTS_TEMPLATE)
        print(f"Created {skill_path.relative_to(root)} and {agents_path.relative_to(root)}")
        print(
            "Add these files to version control so your coding assistant can load the skill."
        )
    return 0


# Keep a ``main`` entry point for backward compatibility with existing
# ``pyproject.toml`` definitions (``repomosaic.cli:main``).  It simply
# forwards to :func:`run` with the current ``sys.argv``.
def main() -> int:
    import sys

    return run(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(run(sys.argv[1:]))
