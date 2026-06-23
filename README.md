# RepoMosaic

RepoMosaic is a Python package that turns an entire Git repository into a code knowledge graph and a contributor skill map.

It is inspired by tools such as Graphify and Understand Anything, but the focus here is repository-level analysis: clone a repository, scan the codebase, create a graph of modules/classes/functions/calls/imports, and use Git history to infer who has worked on which parts of the system.

## What it does now

- Clones a remote Git repository or scans a local repository.
- Parses Python files with the standard `ast` module.
- Builds a directed `networkx` graph containing modules, classes, functions, calls and imports.
- Exports the graph to JSON or GraphML.
- Reads Git commit history and creates a contributor-to-file skill map.
- Provides an extensible base interface for future LLM providers.

## Installation

```bash
pip install -e .
```

Requirements:

- Python 3.9+
- Git installed on your machine
- `networkx`

## CLI usage

Build a graph from a remote repository:

```bash
python -m repomosaic.cli build --repo https://github.com/owner/repo.git --out graph.json
```

Build a GraphML file for tools such as Gephi or Cytoscape:

```bash
python -m repomosaic.cli build --repo /path/to/local/repo --out graph.graphml
```

Generate a contributor skill map:

```bash
python -m repomosaic.cli skills --repo /path/to/local/repo
```

## Python API

```python
from repomosaic import RepoScanner, GraphBuilder, SkillMap

scanner = RepoScanner("https://github.com/owner/repo.git")
repo_path = scanner.ensure_local()
files = scanner.get_files({".py"})

builder = GraphBuilder()
graph = builder.build(files)
builder.save_json("graph.json")

skill_map = SkillMap(repo_path)
skill_map.assign_to_graph(graph)
```

## Current architecture

```text
RepoScanner  -> clone/find repo + collect files
GraphBuilder -> parse source files + create graph
SkillMap     -> read Git history + infer contributor expertise
LLMIntegration -> base interface for future model APIs
```

## Roadmap

- Add Tree-sitter support for JavaScript, TypeScript, Go, Java and Rust.
- Add Neo4j and SQLite exporters.
- Add repository Q&A using OpenAI, Anthropic, Gemini or local models.
- Add richer skill inference from function-level diffs, ownership and review history.
- Add an interactive graph UI.

## License

MIT
