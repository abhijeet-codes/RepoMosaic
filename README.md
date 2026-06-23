# RepoMosaic

RepoMosaic is a lightweight Python library and CLI tool that turns an
entire code repository into a graph of definitions and call
relationships.  It also computes a simple skill map showing which
contributors have touched which files.  RepoMosaic is inspired by
[Graphify](https://github.com/safishamsi/graphify) and
[Understand Anything](https://github.com/isyour/understand-anything),
but aims to be simpler and easier to extend.

**New in 0.2.0** – RepoMosaic now ships as an AI coding assistant skill.  It can be
installed into Claude Code, OpenAI Codex, Cursor, OpenCode and other agents via a
portable `SKILL.md` and `AGENTS.md` integration.  Installing the skill lets
your coding assistant build and consult a project‑wide call graph and skill
map before looking at raw files, dramatically reducing token usage and
improving navigation.  See the *AI assistant integration* section below for
details.

## Features

* **Repository scanning** – clone a remote Git repository or use a
  local directory and collect source files by extension.
* **Call graph generation** – parse Python files into an abstract
  syntax tree (AST) and build a directed graph of functions, classes
  and their call relationships using `networkx`.  Import
  relationships are also captured.
* **Skill mapping** – analyse the Git commit history of the
  repository to determine which authors have edited which files.
* **AI coding assistant integration** – version 0.2.0 adds first‑class
  support for AI coding assistants.  When installed as a skill, RepoMosaic
  automatically builds a call graph and contributor skill map for the
  current project.  Assistants like Claude Code, Codex and Cursor will
  consult these files before invoking file search tools, enabling
  structure‑aware navigation and faster responses.  RepoMosaic writes
  an `AGENTS.md` file and a `.claude/skills/repomosaic/SKILL.md` manifest
  containing detailed guidance for agents.
* **CLI** – build graphs and skill maps from the command line.
* **Extensible LLM support** – stub classes are provided for
  integrating language model APIs with the generated data.

## Installation

Install RepoMosaic from source by cloning the repository and running:

```bash
pip install -e .
```

The package requires Python 3.8 or later and depends on
[`networkx`](https://networkx.org/) for graph construction.  To analyse
Git history the `git` command line tool must be installed and
available on your `PATH`.

## Usage

### Building a call graph

Use the CLI to clone a repository and build a graph:

```bash
python -m repomosaic.cli build --repo https://github.com/python/cpython --out cpython.graphml
```

The output file can be viewed with many graph tools such as
Gephi or Cytoscape.  If no output file is supplied the CLI will
report the number of nodes and edges it found.

### Computing a skill map

Compute which authors edited which files:

```bash
python -m repomosaic.cli skills --repo /path/to/local/repo
```

Each contributor and the files they touched are printed to standard
output along with how many commits they made to that file.

### Programmatic API

You can use RepoMosaic from your own Python scripts:

```python
from repomosaic import RepoScanner, GraphBuilder, SkillMap

# Clone or locate the repository
scanner = RepoScanner("https://github.com/python/cpython")
repo_path = scanner.ensure_local()

# Gather Python files
files = scanner.get_files({".py"})

# Build the graph
builder = GraphBuilder()
graph = builder.build(files)
builder.save_graphml("cpython.graphml")

# Compute and assign skill map
skill_map = SkillMap(repo_path)
skill_map.assign_to_graph(graph)

print("Functions:", len([n for n, d in graph.nodes(data=True) if d.get("type") == "function"]))
```

## Roadmap

RepoMosaic is intentionally minimal to provide a starting point for
more advanced analysis.  Possible future improvements include:

* Parsing and graphing additional languages (JavaScript, TypeScript,
  Go, etc.) via projects like [tree‑sitter](https://tree-sitter.github.io/).
* Exporting graphs to other formats such as Neo4j or SQLite for
  efficient querying.
* Deeper commit analysis to attribute individual functions to authors
  rather than just files.
* Built‑in integrations with OpenAI or other language models.

## AI assistant integration

RepoMosaic v0.2.0 can be installed as an AI coding assistant skill.  It is
compatible with Claude Code, OpenAI Codex, Cursor, OpenCode, Factory Droid
and dozens of other agents that support the open SKILL/AGENTS standards.

When you run the install step, RepoMosaic writes two files into your
project:

* `.claude/skills/repomosaic/SKILL.md` – a manifest file with
  YAML front matter and instructions describing how to invoke RepoMosaic
  from within your coding assistant.  The skill defines a `/repomosaic`
  command that clones or scans a repository, builds a call graph and
  contributor skill map, and outputs JSON files for the agent to read.

* `AGENTS.md` – a universal instruction file that teaches AI coding
  assistants how to work with this project.  In RepoMosaic it explains
  how to build the graph, where to find the output (by default in
  `repomosaic‑out/`), and how to use the graph and skill map to guide
  exploration and assign work.  Agents that do not support PreToolUse
  hooks fall back to reading `AGENTS.md`.

To install the skill for the current project, run:

```bash
python -m repomosaic.cli install --project
```

This will create the `SKILL.md` and `AGENTS.md` files as described above.
After installation, open your AI coding assistant and type `/repomosaic .` to
build the knowledge graph.  The assistant will automatically consult the
generated graph and skill map before reading raw files.

## License

This project is licensed under the MIT License.  See the `LICENSE`
file for details.
