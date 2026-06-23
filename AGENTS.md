# RepoMosaic agent instructions

RepoMosaic is installed in this repository as an AI coding assistant
skill.  Before searching through files, follow these steps to build
and use the knowledge graph:

1. **Build the graph and skill map for this repository**.  From the project root, run:

   ```bash
   python -m repomosaic.cli build --repo . --out repomosaic-out/graph.json
   python -m repomosaic.cli skills --repo . > repomosaic-out/skill_map.json
   ```

   This scans the current repository, constructs a call/import graph
   and exports it as `graph.json`.  It also computes a contributor
   skill map and saves it as `skill_map.json`.

2. **Scan an organisation or user.**  To analyse multiple repositories at
   once, provide the `--owner` flag and optionally a GitHub personal access
   token via `--token` or the `GITHUB_TOKEN` environment variable:

   ```bash
   python -m repomosaic.cli build --owner <owner> --out repomosaic-out/graph.json [--token <pat>]
   python -m repomosaic.cli skills --owner <owner> > repomosaic-out/skill_map.json [--token <pat>]
   ```

   Replace `<owner>` with the organisation or username.  RepoMosaic will
   download and analyse each repository under the owner, merge the graphs and
   skill maps, and write the results to `repomosaic-out/`.  This can take
   time and disk space.

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
Cursor, Trae, **Ollama/Continue** and many others.  Agents that support
pre‑tool hooks will also see a notification when a `repomosaic‑out`
directory exists.  On platforms like Cursor, Trae or local setups via
Ollama, which lack pre‑tool hooks, the contents of this file serve as
the always‑on instructions for graph building and skill mapping.
