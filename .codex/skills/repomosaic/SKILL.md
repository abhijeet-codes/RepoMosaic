---
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
`repomosaic‑out/` and are meant for your coding assistant to consult.
RepoMosaic is similar to Graphify but simpler and focused on Python for now.

## How to use

1. Invoke the skill with `/repomosaic --repo <path-or-url>` to scan a
   single repository (local path or HTTPS URL).  RepoMosaic will build
   a `repomosaic‑out/` directory containing `graph.json`,
   `skill_map.json` and a short `REPORT.md`.

2. To scan an *entire organisation* or user, invoke `/repomosaic --owner <name>`.
   Optionally pass `--token <pat>` if the repositories are private or
   you want to avoid rate limits.  RepoMosaic will iterate through
   all repositories belonging to the owner, build individual graphs
   and skill maps and merge them.  The aggregated files are written to
   `repomosaic‑out/` and can be large for big organisations.

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
