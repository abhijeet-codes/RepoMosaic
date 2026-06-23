"""Repository location, clone and file discovery utilities."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Optional


class RepoScanner:
    """Clone or locate a repository and enumerate files by extension."""

    def __init__(self, repo_url_or_path: str, *, local_dir: Optional[str] = None, clone: bool = True) -> None:
        self.repo_url_or_path = repo_url_or_path
        self.local_dir = local_dir
        self.clone = clone
        self._path: Optional[Path] = None

    def ensure_local(self) -> Path:
        """Return a local repository path, cloning remote URLs when needed."""
        if self._path is not None:
            return self._path

        candidate = Path(self.repo_url_or_path)
        if candidate.exists() and candidate.is_dir():
            self._path = candidate.resolve()
            return self._path

        if not self.clone:
            raise ValueError("No local repository path found and clone=False was supplied.")

        clone_root = Path(self.local_dir) if self.local_dir else Path(tempfile.mkdtemp(prefix="repomosaic-"))
        clone_root.mkdir(parents=True, exist_ok=True)
        repo_name = os.path.basename(self.repo_url_or_path.rstrip("/")).replace(".git", "")
        destination = clone_root / repo_name
        if destination.exists():
            self._path = destination.resolve()
            return self._path

        cmd = ["git", "clone", "--depth", "1", self.repo_url_or_path, str(destination)]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as exc:
            raise RuntimeError("git must be installed to clone repositories.") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.decode("utf-8", errors="replace")) from exc

        self._path = destination.resolve()
        return self._path

    def get_files(self, extensions: Optional[Iterable[str]] = None) -> list[Path]:
        """Return files in the repository matching the requested extensions."""
        repo_path = self.ensure_local()
        allowed = {e.lower() for e in extensions} if extensions is not None else None
        files: list[Path] = []
        for root, dirs, names in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "node_modules"}]
            for name in names:
                path = Path(root) / name
                if allowed is None or path.suffix.lower() in allowed:
                    files.append(path)
        return files
