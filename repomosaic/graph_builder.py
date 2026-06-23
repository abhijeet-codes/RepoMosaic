"""Build a repository knowledge graph from Python source files."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Iterable, Optional

import networkx as nx


class PythonGraphVisitor(ast.NodeVisitor):
    """Collect definitions, imports and calls from one Python module."""

    def __init__(self, module: str, file_path: Path) -> None:
        self.module = module
        self.file_path = file_path
        self.nodes: dict[str, dict[str, object]] = {}
        self.edges: list[tuple[str, str, str]] = []
        self.context: list[str] = []

    def _qualname(self, name: str) -> str:
        return ".".join([self.module, *self.context, name])

    def _current(self) -> str:
        if not self.context:
            self.nodes.setdefault(self.module, {"type": "module", "file": str(self.file_path), "lineno": 1})
            return self.module
        return ".".join([self.module, *self.context])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        name = self._qualname(node.name)
        self.nodes[name] = {
            "type": "function",
            "file": str(self.file_path),
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", None),
        }
        self.context.append(node.name)
        self.generic_visit(node)
        self.context.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        name = self._qualname(node.name)
        self.nodes[name] = {
            "type": "class",
            "file": str(self.file_path),
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", None),
        }
        self.context.append(node.name)
        self.generic_visit(node)
        self.context.pop()

    def visit_Call(self, node: ast.Call) -> None:
        target = self._call_name(node.func)
        if target:
            self.edges.append((self._current(), target, "call"))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.edges.append((self._current(), alias.name, "import"))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            target = f"{module}.{alias.name}" if module else alias.name
            self.edges.append((self._current(), target, "import"))

    def _call_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return f"{self.module}.{node.id}"
        if isinstance(node, ast.Attribute):
            return f"{self.module}.{node.attr}"
        return None


class GraphBuilder:
    """Build and export a directed graph of repository structure."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def build(self, files: Iterable[Path]) -> nx.DiGraph:
        """Parse Python files and return a NetworkX DiGraph."""
        for path in files:
            path = Path(path)
            if path.suffix.lower() != ".py":
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue

            visitor = PythonGraphVisitor(path.stem, path)
            visitor.visit(tree)
            for node, attrs in visitor.nodes.items():
                self.graph.add_node(node, **attrs)
            for source, target, kind in visitor.edges:
                if source not in self.graph:
                    self.graph.add_node(source, type="unknown", file=str(path))
                if target not in self.graph:
                    self.graph.add_node(target, type="external", file="")
                if self.graph.has_edge(source, target):
                    self.graph[source][target]["count"] += 1
                else:
                    self.graph.add_edge(source, target, kind=kind, count=1)
        return self.graph

    def save_graphml(self, path: str) -> None:
        """Write the graph as GraphML."""
        nx.write_graphml(self.graph, path)

    def save_json(self, path: str) -> None:
        """Write the graph as JSON with nodes and edges arrays."""
        data = {
            "nodes": [{"id": n, **attrs} for n, attrs in self.graph.nodes(data=True)],
            "edges": [{"source": u, "target": v, **attrs} for u, v, attrs in self.graph.edges(data=True)],
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
