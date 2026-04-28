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
        paren_depth = 0
        bracket_depth = 0

        for char in body:
            if char == "," and paren_depth == 0 and bracket_depth == 0:
                goals.append(buffer.strip())
                buffer = ""
                continue

            buffer += char
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth = max(0, paren_depth - 1)
            elif char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth = max(0, bracket_depth - 1)

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

    def _resolve_value(self, token: str, substitution: Dict[str, str]) -> str:
        seen = set()
        current = token.strip()
        while current in substitution and current not in seen:
            seen.add(current)
            current = substitution[current].strip()
        return current

    def _unify_terms(self, left: str, right: str, substitution: Dict[str, str]) -> bool:
        left = self._resolve_value(left, substitution)
        right = self._resolve_value(right, substitution)

        if left == right:
            return True

        if self._is_variable(left):
            substitution[left] = right
            return True

        if self._is_variable(right):
            substitution[right] = left
            return True

        left_functor, left_args = self._parse_term(left)
        right_functor, right_args = self._parse_term(right)
        if left_args or right_args:
            if left_functor != right_functor or len(left_args) != len(right_args):
                return False
            return all(self._unify_terms(a, b, substitution) for a, b in zip(left_args, right_args))

        return False

    def _unify_goal_with_head(self, goal: str, head: str) -> Optional[Dict[str, str]]:
        goal_functor, goal_args = self._parse_term(goal)
        head_functor, head_args = self._parse_term(head)
        if goal_functor != head_functor or len(goal_args) != len(head_args):
            return None

        substitution: Dict[str, str] = {}
        for head_arg, goal_arg in zip(head_args, goal_args):
            if not self._unify_terms(head_arg, goal_arg, substitution):
                return None

        return substitution

    def _apply_substitution(self, text: str, substitution: Dict[str, str]) -> str:
        pattern = re.compile(r"\b([A-Z_][A-Za-z0-9_]*)\b")
        previous = None
        result = text
        while result != previous:
            previous = result
            result = pattern.sub(
                lambda match: self._resolve_value(match.group(1), substitution),
                result,
            )
        return result

    def _format_substitution(self, substitution: Optional[Dict[str, str]]) -> str:
        if not substitution:
            return "{}"
        return "{" + ", ".join(f"{var}→{val}" for var, val in substitution.items()) + "}"

    def _format_standardization(self, mapping: Dict[str, str]) -> str:
        if not mapping:
            return "{}"
        return "{" + ", ".join(f"{orig}→{new}" for orig, new in mapping.items()) + "}"

    def _query_preview(self, goal: str, max_results: int = 3) -> List[Dict[str, Any]]:
        try:
            return self.query(goal, max_results=max_results)
        except Exception:
            return []

    def _build_external_goal_node(self, goal: str) -> Dict[str, Any]:
        answers = self._query_preview(goal)
        node: Dict[str, Any] = {
            "goal": goal,
            "status": "prolog_goal" if answers else "failed",
            "result": "success" if answers else "failed",
            "children": [],
        }
        if answers:
            node["answers"] = answers
        return node

    def _delegate_to_prolog(self, goal: str) -> bool:
        goal_key = self._goal_key(goal)
        return (
            goal_key in {"is_list", "nonvar", "call", "map_result", "my_member"}
            or goal.startswith("(")
            or goal.startswith("\\+")
            or "=" in goal
        )

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

        if goal == "!":
            node["status"] = "cut"
            node["result"] = "success"
            return node

        if self._delegate_to_prolog(goal):
            return self._build_external_goal_node(goal)

        clause_key = self._goal_key(goal)
        clauses = self.clauses.get(clause_key, [])
        if not clauses:
            return self._build_external_goal_node(goal)

        for clause_index, clause in enumerate(clauses, start=1):
            standardized = self._standardize_clause(clause, depth * 1000 + clause_index)
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
                attempt["answers"] = self._query_preview(goal)
            else:
                all_success = True
                cut_seen = False
                current_substitution = dict(substitution)
                for subgoal in standardized["body"]:
                    instantiated_subgoal = self._apply_substitution(subgoal, current_substitution)
                    if instantiated_subgoal == "!":
                        cut_seen = True
                    child = self._build_sld_tree(instantiated_subgoal, depth + 1, visited + [goal], max_depth)
                    attempt["children"].append(child)
                    if child.get("result") != "success":
                        all_success = False
                        break
                    child_answers = child.get("answers") or []
                    if len(child_answers) == 1:
                        for key, value in child_answers[0].items():
                            current_substitution[key] = str(value)
                attempt["status"] = "rule"
                attempt["result"] = "success" if all_success else "failed"
                if all_success:
                    attempt["answers"] = self._query_preview(goal)

            node["children"].append(attempt)
            if attempt.get("result") == "success" and cut_seen:
                break

        for idx, child in enumerate(node["children"]):
            if child["result"] == "failed" and any(later["result"] == "success" for later in node["children"][idx + 1 :]):
                child["backtracking"] = "backtracked"

        node["result"] = "success" if any(child["result"] == "success" for child in node["children"]) else "failed"
        node["status"] = node["result"]
        if node["result"] == "success":
            node["answers"] = self._query_preview(goal)
        return node
