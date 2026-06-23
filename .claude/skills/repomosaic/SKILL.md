---
name: repomosaic
version: 0.2.0
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
