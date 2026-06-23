# RepoMosaic agent instructions

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
including Claude Code, OpenAI Codex, Cursor and many others.  Agents
that support pre‑tool hooks will also see a notification when a
`repomosaic-out` directory exists.
