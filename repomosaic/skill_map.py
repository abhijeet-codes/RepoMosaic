"""Build contributor skill maps from Git history."""
from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Mapping


class SkillMap:
    """Infer contributor ownership from commit history."""

    def __init__(self, repo_path: str | Path) -> None:
        self.repo_path = Path(repo_path).resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"{self.repo_path} is not a Git repository")

    def _git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise RuntimeError("git must be installed to compute skill maps") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip()) from exc
        return result.stdout

    def compute(self) -> Mapping[str, dict[str, int]]:
        """Return {author: {file_path: touched_commit_count}}."""
        output = self._git(["log", "--pretty=format:%H|%an", "--name-only"])
        authors: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        current_author: str | None = None
        for raw in output.splitlines():
            line = raw.strip()
            if not line:
                continue
            if "|" in line:
                _, current_author = line.split("|", 1)
                continue
            if current_author:
                authors[current_author][line] += 1
        return authors

    def assign_to_graph(self, graph) -> None:
        """Attach a skills dict to each graph node based on the node file."""
        data = self.compute()
        for node, attrs in graph.nodes(data=True):
            file_value = attrs.get("file")
            if not file_value:
                continue
            try:
                rel_path = str(Path(str(file_value)).resolve().relative_to(self.repo_path))
            except ValueError:
                rel_path = str(file_value)
            graph.nodes[node]["skills"] = {
                author: files[rel_path]
                for author, files in data.items()
                if rel_path in files
            }
