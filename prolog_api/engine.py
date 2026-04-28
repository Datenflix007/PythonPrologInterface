from pathlib import Path
from typing import Any, Dict, List, Optional
from pyswip import Prolog


class PrologEngine:
    """
    Kapselt SWI-Prolog/PySwip.
    Kann in verschiedenen Projekten wiederverwendet werden.
    """

    def __init__(self, knowledge_file: str | Path):
        self.knowledge_file = Path(knowledge_file).resolve()
        if not self.knowledge_file.exists():
            raise FileNotFoundError(f"Prolog-Datei nicht gefunden: {self.knowledge_file}")

        self.prolog = Prolog()
        self.prolog.consult(str(self.knowledge_file))
        self.clauses = self._parse_clauses()

    def query(self, query_text: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Führt eine Prolog-Query aus.

        Beispiel:
            engine.query("role(Person, developer)")
        """
        results = []

        for index, solution in enumerate(self.prolog.query(query_text)):
            if max_results is not None and index >= max_results:
                break
            results.append(dict(solution))

        return results

    def ask_one(self, query_text: str) -> Optional[Dict[str, Any]]:
        """
        Gibt nur die erste Lösung zurück.
        """
        result = self.query(query_text, max_results=1)
        return result[0] if result else None

    def is_true(self, query_text: str) -> bool:
        """
        Prüft, ob eine Prolog-Aussage erfüllbar ist.
        """
        return bool(self.query(query_text, max_results=1))

    def explain_query(self, query_text: str, max_depth: int = 6) -> Dict[str, Any]:
        """
        Gibt eine einfache SLD-Resolutionserklärung für eine Query zurück.
        Die Darstellung basiert auf der geladenen Wissensbasis und zeigt die
        aufgerufenen Klauseln und Unterziele.
        """
        return {
            "query": query_text,
            "tree": self._build_sld_tree(query_text.strip(), 0, [], max_depth)
        }

    def _parse_clauses(self) -> Dict[str, List[tuple[str, List[str]]]]:
        clauses: Dict[str, List[tuple[str, List[str]]]] = {}
        text = self.knowledge_file.read_text(encoding="utf-8")
        current = ""

        for raw_line in text.splitlines():
            line = raw_line.split("%", 1)[0].strip()
            if not line:
                continue

            current += " " + line
            if current.strip().endswith("."):
                clause_text = current.strip()[:-1].strip()
                current = ""
                if not clause_text:
                    continue

                if ":-" in clause_text:
                    head, body = clause_text.split(":-", 1)
                    body_goals = self._split_goals(body)
                else:
                    head = clause_text
                    body_goals = []

                clause_key = self._goal_key(head)
                clauses.setdefault(clause_key, []).append((head.strip(), body_goals))

        return clauses

    def _split_goals(self, body: str) -> List[str]:
        body = body.strip()
        if not body:
            return []

        goals: List[str] = []
        buffer = ""
        depth = 0

        for char in body:
            if char == "," and depth == 0:
                goals.append(buffer.strip())
                buffer = ""
                continue

            buffer += char
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)

        if buffer.strip():
            goals.append(buffer.strip())

        return goals

    def _goal_key(self, term: str) -> str:
        term = term.strip()
        if "(" in term:
            return term[: term.index("(")].strip()
        return term

    def _build_sld_tree(self, goal: str, depth: int, visited: List[str], max_depth: int) -> Dict[str, Any]:
        node: Dict[str, Any] = {"goal": goal}

        if depth >= max_depth:
            node["status"] = "max_depth_reached"
            return node

        if goal in visited:
            node["status"] = "cycle_detected"
            return node

        clause_key = self._goal_key(goal)
        available_clauses = self.clauses.get(clause_key, [])
        if not available_clauses:
            node["status"] = "unknown_goal"
            return node

        head, body_goals = available_clauses[0]
        node["clause"] = head

        if not body_goals:
            node["status"] = "fact"
            node["children"] = []
            return node

        node["status"] = "rule"
        node["children"] = [
            self._build_sld_tree(subgoal, depth + 1, visited + [goal], max_depth)
            for subgoal in body_goals
        ]
        return node
