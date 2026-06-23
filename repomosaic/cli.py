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
import json
import urllib.request
import os
from pathlib import Path
from typing import Sequence, List, Dict


def list_repo_urls(owner: str, token: str | None = None) -> List[str]:
    """Return a list of HTTPS clone URLs for all repositories under a GitHub owner.

    The owner may be a user or an organization.  If a token is provided it
    will be used for authentication.  Only the first page of repositories
    (up to 100) is returned.  If no repositories are found an empty list
    is returned.

    Parameters
    ----------
    owner: str
        GitHub organization name or username.
    token: str | None
        Optional GitHub personal access token for authenticated requests.

    Returns
    -------
    List[str]
        List of clone URLs for the repositories belonging to the owner.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # Try organization endpoint first
    urls: List[str] = []
    for endpoint in [f"https://api.github.com/orgs/{owner}/repos?per_page=100", f"https://api.github.com/users/{owner}/repos?per_page=100"]:
        req = urllib.request.Request(endpoint, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, list):
                    urls = [repo.get("clone_url") for repo in data if repo.get("clone_url")]
                    if urls:
                        return urls
        except Exception:
            # Continue to next endpoint on any error
            continue
    return urls


from .repo_scanner import RepoScanner
from .graph_builder import GraphBuilder
from .skill_map import SkillMap

# Templates for AI assistant integration.  These are simple static files
# written during ``install --project``.  The templates replicate the
# committed versions in the repository and document how agents should
# invoke RepoMosaic.

SKILL_TEMPLATE = """---
name: repomosaic
version: 0.4.0
description: Build a call graph and contributor skill map from one or many repositories.
author: RepoMosaic Developers
trigger: "/repomosaic"
args: |
  repo: string (optional)  # Path or HTTPS URL to a single repository
  owner: string (optional)  # GitHub organization or username to scan all repositories
  token: string (optional)  # Personal access token for GitHub API when using --owner
  out: string (optional)  # Output directory for graph and skill map (default: repomosaic-out/)
returns: |
  repomosaic-out/graph.json  # JSON representation of the call/import graph
  repomosaic-out/skill_map.json  # JSON contributor skill map
---

# RepoMosaic Skill

RepoMosaic is a Python package and CLI tool that turns a repository
into a call graph and skill map.  When invoked via `/repomosaic`, it
can scan a single repository or **an entire GitHub organisation or
user**.  RepoMosaic will clone or download each repository, build
AST‑based call/import graphs using NetworkX, analyse the Git
history to assign commit‑based skills to contributors, and combine
the results into a single graph and skill map.  These files live in
`repomosaic-out/` and are meant for your coding assistant to consult.
RepoMosaic is similar to Graphify but simpler and focused on Python for now.

## How to use

1. Invoke the skill with `/repomosaic --repo <path-or-url>` to scan a
   single repository (local path or HTTPS URL).  RepoMosaic will build
   a `repomosaic-out/` directory containing `graph.json`,
   `skill_map.json` and a short `REPORT.md`.

2. To scan an *entire organisation* or user, invoke `/repomosaic --owner <name>`.
   Optionally pass `--token <pat>` if the repositories are private or
   you want to avoid rate limits.  RepoMosaic will iterate through
   all repositories belonging to the owner, build individual graphs
   and skill maps and merge them.  The aggregated files are written to
   `repomosaic-out/` and can be large for big organisations.

3. Once the graph is built, you can ask your assistant high‑level
   questions such as "list all functions in module X" or "which
   contributor worked most on file Y?" — the assistant should inspect
   `graph.json` and `skill_map.json` rather than grepping through raw
   files.

## Safety

RepoMosaic only interacts with Git over HTTPS and performs static
analysis via Python's `ast` module.  It never executes arbitrary code
from the repository.  LLM integration is optional and disabled by
default.  When scanning multiple repositories, RepoMosaic may
download a significant amount of data, so ensure you have disk space
and network bandwidth.
"""

AGENTS_TEMPLATE = """# RepoMosaic agent instructions

RepoMosaic is installed in this repository as an AI coding assistant
skill.  Before searching through files, follow these steps to build
and use the knowledge graph:

1. **Build the graph and skill map for this project** (single repository).  From the project root, run:

   ```bash
   python -m repomosaic.cli build --repo . --out repomosaic-out/graph.json
   python -m repomosaic.cli skills --repo . > repomosaic-out/skill_map.json
   ```

   This scans the current repository, constructs a call/import graph
   and exports it as `graph.json`.  It also computes a contributor
   skill map and saves it as `skill_map.json`.

2. **Scan an entire organisation or user.**  If the user wants to
   analyse all repositories under a GitHub owner, run:

   ```bash
   python -m repomosaic.cli build --owner <owner> --out repomosaic-out/graph.json [--token <pat>]
   python -m repomosaic.cli skills --owner <owner> > repomosaic-out/skill_map.json [--token <pat>]
   ```

   Replace `<owner>` with the organisation or username.  Provide a
   personal access token via `--token` or the `GITHUB_TOKEN`
   environment variable to access private repositories or to increase
   API rate limits.  RepoMosaic will download each repository,
   generate individual graphs and combine them into a single
   aggregated graph and skill map.  Note that this can take some
   time and disk space for large organisations.

3. **Consult the outputs.**  Use the generated files to guide your
   exploration and planning:

   * `graph.json` lists nodes (functions, classes, modules) and edges
     (calls, imports).  Inspect node attributes to understand
     relationships and dependencies.
   * `skill_map.json` lists each contributor and the files they
     touched, along with commit counts.

4. **Ask RepoMosaic for help.**  When asked to explain a module or
   identify who wrote a piece of code, prefer reading
   `graph.json` and `skill_map.json` instead of scanning raw
   files.  The assistant should reference these structures to answer
   questions more accurately and with fewer tokens.

5. **Do not execute repository code.**  RepoMosaic builds graphs
   statically via AST parsing.  It should not be used to run or test
   arbitrary code.

These instructions apply to any coding agent that reads `AGENTS.md`,
including GitHub Copilot Chat, Code Pilot, Claude Code, OpenAI Codex CLI,
Cursor, Trae, **Ollama** and many others.  Agents that support pre‑tool hooks will
also see a notification when a `repomosaic-out` directory exists.  On
platforms like Cursor or Trae, which lack pre‑tool hooks, the contents
of this file serve as the always‑on instructions for graph building and
skill mapping.  For local LLM setups via Ollama or Continue, this file
provides the guidance needed to build and query the RepoMosaic graph.
"""


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RepoMosaic CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build command
    build_parser = subparsers.add_parser("build", help="Build a call graph from a repository or owner")
    build_parser.add_argument(
        "--repo",
        help="Path or Git URL to the repository. If provided together with --owner, --owner takes precedence.",
    )
    build_parser.add_argument(
        "--owner",
        help="GitHub organization or username to scan. When supplied, all repositories under this owner will be downloaded and combined into a single graph.",
    )
    build_parser.add_argument(
        "--token",
        help="GitHub personal access token for API calls when using --owner. Defaults to the GITHUB_TOKEN environment variable.",
    )
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
    skills_parser = subparsers.add_parser("skills", help="Compute a skill map for a repository or owner")
    skills_parser.add_argument(
        "--repo",
        help="Path to a local Git repository. If provided together with --owner, --owner takes precedence.",
    )
    skills_parser.add_argument(
        "--owner",
        help="GitHub organization or username to scan. When supplied, all repositories under this owner will be downloaded and aggregated into a single skill map.",
    )
    skills_parser.add_argument(
        "--token",
        help="GitHub personal access token for API calls when using --owner. Defaults to the GITHUB_TOKEN environment variable.",
    )

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
        # Determine if we are building from a single repository or an owner
        if args.owner:
            owner = args.owner
            token = args.token or os.environ.get("GITHUB_TOKEN")
            try:
                repo_urls = list_repo_urls(owner, token)
            except Exception as e:
                print(f"Error listing repositories for owner '{owner}': {e}")
                return 1
            if not repo_urls:
                print(f"No repositories found for owner '{owner}'")
                return 1
            # Build graphs for each repository and merge them
            import networkx as nx  # imported lazily to avoid dependency when not needed
            graphs: List[nx.DiGraph] = []
            for repo_url in repo_urls:
                scanner = RepoScanner(repo_url)
                repo_path = scanner.ensure_local()
                files = scanner.get_files(args.ext)
                builder = GraphBuilder()
                g = builder.build(files)
                graphs.append(g)
            if not graphs:
                print(f"No supported files found across repositories for owner '{owner}'")
                return 1
            aggregated_graph = nx.compose_all(graphs)
            # Use a fresh builder wrapper to save aggregated graph
            builder = GraphBuilder()
            builder.graph = aggregated_graph
            if args.out:
                out_path = Path(args.out)
                if out_path.suffix.lower() == ".graphml":
                    builder.save_graphml(str(out_path))
                else:
                    builder.save_json(str(out_path))
                print(f"Aggregated graph written to {out_path}")
            else:
                print("Aggregated graph built with", len(aggregated_graph.nodes), "nodes and", len(aggregated_graph.edges), "edges")
        else:
            # Single repository
            if not args.repo:
                print("--repo is required when --owner is not provided")
                return 1
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
        if args.owner:
            owner = args.owner
            token = args.token or os.environ.get("GITHUB_TOKEN")
            try:
                repo_urls = list_repo_urls(owner, token)
            except Exception as e:
                print(f"Error listing repositories for owner '{owner}': {e}")
                return 1
            if not repo_urls:
                print(f"No repositories found for owner '{owner}'")
                return 1
            from collections import defaultdict
            aggregated: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for repo_url in repo_urls:
                scanner = RepoScanner(repo_url)
                repo_path = scanner.ensure_local()
                # compute skill map for each repo
                sm = SkillMap(str(repo_path)).compute()
                for author, files_dict in sm.items():
                    for file_path, count in files_dict.items():
                        aggregated[author][file_path] += count
            for author, files_dict in aggregated.items():
                print(author)
                for file_path, count in files_dict.items():
                    print(f"  {file_path}: {count}")
        else:
            if not args.repo:
                print("--repo is required when --owner is not provided")
                return 1
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
