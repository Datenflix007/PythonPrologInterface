from pathlib import Path
from typing import Any, Dict, List, Optional
import re
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

    def explain_query(self, query_text: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        Gibt eine SLD-Resolutionserklärung für eine Query zurück.
        """
        return {
            "query": query_text,
            "tree": self._build_sld_tree(query_text.strip(), 0, [], max_depth)
        }

    def _parse_clauses(self) -> Dict[str, List[Dict[str, Any]]]:
        clauses: Dict[str, List[Dict[str, Any]]] = {}
        text = self.knowledge_file.read_text(encoding="utf-8")
        current = ""
        current_line = 0

        for index, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.split("%", 1)[0].strip()
            if not line:
                continue

            if not current:
                current_line = index

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
                clauses.setdefault(clause_key, []).append({
                    "head": head.strip(),
                    "body": [goal.strip() for goal in body_goals],
                    "line": current_line,
                })

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

    def _find_variables(self, text: str) -> List[str]:
        return [
            match.group(0)
            for match in re.finditer(r"[A-Z][A-Za-z0-9_]*", text)
        ]

    def _replace_vars(self, text: str, mapping: Dict[str, str]) -> str:
        pattern = re.compile(r"([A-Z][A-Za-z0-9_]*)")
        return pattern.sub(lambda match: mapping.get(match.group(1), match.group(1)), text)

    def _standardize_clause(self, clause: Dict[str, Any], clause_id: int) -> Dict[str, Any]:
        vars_in_clause: List[str] = []
        for part in [clause["head"]] + clause["body"]:
            for var in self._find_variables(part):
                if var not in vars_in_clause:
                    vars_in_clause.append(var)

        mapping: Dict[str, str] = {}
        for count, var in enumerate(vars_in_clause, start=1):
            mapping[var] = f"{var}_{clause_id}"

        return {
            "head": self._replace_vars(clause["head"], mapping),
            "body": [self._replace_vars(goal, mapping) for goal in clause["body"]],
            "line": clause["line"],
            "standardization": mapping,
        }

    def _parse_term(self, term_text: str) -> tuple[str, List[str]]:
        term_text = term_text.strip()
        if "(" not in term_text:
            return term_text, []
        functor = term_text[: term_text.index("(")].strip()
        args_text = term_text[term_text.index("(") + 1 : -1]
        return functor, self._split_goals(args_text)

    def _is_variable(self, token: str) -> bool:
        return bool(re.match(r"^[A-Z_][A-Za-z0-9_]*$", token))

    def _unify_goal_with_head(self, goal: str, head: str) -> Optional[Dict[str, str]]:
        goal_functor, goal_args = self._parse_term(goal)
        head_functor, head_args = self._parse_term(head)
        if goal_functor != head_functor or len(goal_args) != len(head_args):
            return None

        substitution: Dict[str, str] = {}
        for head_arg, goal_arg in zip(head_args, goal_args):
            head_arg = head_arg.strip()
            goal_arg = goal_arg.strip()
            if self._is_variable(head_arg):
                substitution[head_arg] = goal_arg
            elif head_arg != goal_arg:
                return None

        return substitution

    def _format_substitution(self, substitution: Optional[Dict[str, str]]) -> str:
        if not substitution:
            return "{}"
        return "{" + ", ".join(f"{var}→{val}" for var, val in substitution.items()) + "}"

    def _format_standardization(self, mapping: Dict[str, str]) -> str:
        if not mapping:
            return "{}"
        return "{" + ", ".join(f"{orig}→{new}" for orig, new in mapping.items()) + "}"

    def _build_sld_tree(self, goal: str, depth: int, visited: List[str], max_depth: int) -> Dict[str, Any]:
        node: Dict[str, Any] = {"goal": goal, "status": "pending", "children": []}

        if depth >= max_depth:
            node["status"] = "max_depth_reached"
            node["result"] = "unknown"
            return node

        if goal in visited:
            node["status"] = "cycle_detected"
            node["result"] = "failed"
            return node

        clause_key = self._goal_key(goal)
        clauses = self.clauses.get(clause_key, [])
        if not clauses:
            node["status"] = "unknown_goal"
            node["result"] = "failed"
            return node

        for clause_index, clause in enumerate(clauses, start=1):
            standardized = self._standardize_clause(clause, clause_index)
            substitution = self._unify_goal_with_head(goal, standardized["head"])

            attempt: Dict[str, Any] = {
                "goal": goal,
                "clause": standardized["head"],
                "line_number": clause["line"],
                "substitution": self._format_substitution(substitution),
                "standardization": self._format_standardization(standardized["standardization"]),
                "edge_label": f"Zeile {clause['line']} | σ={self._format_substitution(substitution)} | std={self._format_standardization(standardized['standardization'])}",
                "children": [],
            }

            if substitution is None:
                attempt["status"] = "no_unify"
                attempt["result"] = "failed"
            elif not standardized["body"]:
                attempt["status"] = "fact"
                attempt["result"] = "success"
            else:
                all_success = True
                for subgoal in standardized["body"]:
                    child = self._build_sld_tree(subgoal, depth + 1, visited + [goal], max_depth)
                    attempt["children"].append(child)
                    if child.get("result") != "success":
                        all_success = False
                attempt["status"] = "rule"
                attempt["result"] = "success" if all_success else "failed"

            node["children"].append(attempt)

        for idx, child in enumerate(node["children"]):
            if child["result"] == "failed" and any(later["result"] == "success" for later in node["children"][idx + 1 :]):
                child["backtracking"] = "backtracked"

        node["result"] = "success" if any(child["result"] == "success" for child in node["children"]) else "failed"
        node["status"] = node["result"]
        return node
