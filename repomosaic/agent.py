"""
agent.py
=========

This module defines a simple agent class for orchestrating RepoMosaic
operations and integrating with language models.  The
``RepoMosaicAgent`` can build aggregated graphs and skill maps across an
entire GitHub organisation or user and optionally answer
questions using a supplied language model integration.

The agent is intentionally minimal: it uses the existing ``RepoScanner``,
``GraphBuilder`` and ``SkillMap`` classes to perform its work and
expects an ``LLMIntegration`` implementation to handle natural
language interaction.  See ``llm_integration.py`` for more on how to
implement a custom language model connector.

Example usage::

    from repomosaic.agent import RepoMosaicAgent
    from repomosaic.llm_integration import LLMIntegration

    # create an agent with a custom LLM integration
    agent = RepoMosaicAgent(llm=my_llm)
    # build aggregated graph and skill map for an organisation
    outputs = agent.build_organisation("my-org", token=os.environ.get("GITHUB_TOKEN"))
    # ask a question about the codebase
    answer = agent.answer("Which repositories implement OAuth?", [
        f"Graph path: {outputs['graph']}",
        f"Skill map: {outputs['skill_map']}"
    ])

Note that the ``answer`` method is a simple wrapper that passes your
question and context to the LLM's summarisation API.  You can extend
this class to include more sophisticated prompt templates or retrieval
steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any, List

import networkx as nx

from .cli import list_repo_urls
from .repo_scanner import RepoScanner
from .graph_builder import GraphBuilder
from .skill_map import SkillMap
from .llm_integration import LLMIntegration


class RepoMosaicAgent:
    """High‑level orchestrator for RepoMosaic tasks.

    The agent can build aggregated call graphs and skill maps for all
    repositories belonging to a GitHub organisation or user.  It can also
    answer natural language questions by delegating to a language model
    integration.
    """

    def __init__(self, llm: Optional[LLMIntegration] = None) -> None:
        """Initialise the agent.

        Parameters
        ----------
        llm: LLMIntegration | None
            Optional language model integration used to answer questions.
            If not provided, the ``answer`` method will raise an error.
        """
        self.llm = llm

    def build_organisation(self, owner: str, token: Optional[str] = None, out_dir: str = "repomosaic-out") -> Dict[str, Path]:
        """Build aggregated graph and skill map for all repositories under an owner.

        This method lists all repositories belonging to the given GitHub
        organisation or user (public by default, private if a token is
        provided), clones or updates them locally, constructs call/import
        graphs and skill maps for each, merges them into a single graph and
        skill map, and writes the results to the specified output directory.

        Parameters
        ----------
        owner: str
            GitHub organisation name or username.
        token: str | None
            Optional personal access token to authenticate GitHub API calls.
        out_dir: str
            Directory where the aggregated graph and skill map will be
            written.  Defaults to ``repomosaic-out``.

        Returns
        -------
        Dict[str, Path]
            Paths to the generated ``graph.json`` and ``skill_map.json``.
        """
        repo_urls = list_repo_urls(owner, token)
        graphs: List[nx.DiGraph] = []
        aggregated_skills: Dict[str, Dict[str, int]] = {}
        for url in repo_urls:
            scanner = RepoScanner(url)
            repo_path = scanner.ensure_local()
            files = scanner.get_files([".py"])
            builder = GraphBuilder()
            g = builder.build(files)
            graphs.append(g)
            skills = SkillMap(str(repo_path)).compute()
            # merge skill maps
            for author, files_dict in skills.items():
                aggregated_skills.setdefault(author, {})
                for path, count in files_dict.items():
                    aggregated_skills[author][path] = aggregated_skills[author].get(path, 0) + count
        if graphs:
            agg_graph = nx.compose_all(graphs)
            out_dir_path = Path(out_dir)
            out_dir_path.mkdir(parents=True, exist_ok=True)
            graph_path = out_dir_path / "graph.json"
            builder = GraphBuilder()
            builder.graph = agg_graph
            builder.save_json(str(graph_path))
            skills_path = out_dir_path / "skill_map.json"
            import json
            with skills_path.open("w") as f:
                json.dump(aggregated_skills, f, indent=2)
            return {"graph": graph_path, "skill_map": skills_path}
        else:
            raise RuntimeError(f"No repositories found for owner '{owner}'")

    def answer(self, question: str, context: List[str]) -> str:
        """Answer a question using the attached language model.

        The implementation concatenates the question and context and
        delegates to the ``summarise`` method of the provided LLM
        integration.  Subclasses can override this method to provide
        more sophisticated prompting.

        Parameters
        ----------
        question: str
            The natural language question to answer.
        context: List[str]
            A list of context strings (such as file paths or summaries) to
            include alongside the question when querying the LLM.

        Returns
        -------
        str
            The LLM's response.
        """
        if not self.llm:
            raise RuntimeError("No LLMIntegration provided for answering questions")
        prompt = question + "\n\n" + "\n".join(context)
        summaries = self.llm.summarise([prompt])
        return summaries[0] if summaries else ""
