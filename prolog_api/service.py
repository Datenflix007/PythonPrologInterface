from pathlib import Path
from typing import Any, Dict, List, Optional
from .engine import PrologEngine


class PrologService:
    """
    Höhere Anwendungsschicht.
    Hier definierst du projektspezifische Methoden,
    damit andere Python-Dateien nicht direkt Prolog-Queries bauen müssen.
    """

    def __init__(self, knowledge_file: str | Path):
        self.engine = PrologEngine(knowledge_file)

    def raw_query(self, query_text: str) -> List[Dict[str, Any]]:
        return self.engine.query(query_text)

    def get_people_by_role(self, role: str) -> List[str]:
        query = f"role(Person, {role})"
        results = self.engine.query(query)
        return [str(row["Person"]) for row in results]

    def get_people_with_skill(self, skill: str) -> List[str]:
        query = f"has_skill(Person, {skill})"
        results = self.engine.query(query)
        return [str(row["Person"]) for row in results]

    def get_project_members(self, project: str) -> List[str]:
        query = f"works_on(Person, {project})"
        results = self.engine.query(query)
        return [str(row["Person"]) for row in results]

    def is_person_suitable_for_project(self, person: str, project: str) -> bool:
        query = f"suitable_for_project({person}, {project})"
        return self.engine.is_true(query)

    def explain_query(self, query_text: str) -> Dict[str, Any]:
        return self.engine.explain_query(query_text)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generische Schnittstelle für andere Python-Kontexte.

        Beispiel:
            {
                "action": "people_with_skill",
                "params": {"skill": "python"}
            }
        """
        action = request.get("action")
        params = request.get("params", {})

        try:
            if action == "people_by_role":
                data = self.get_people_by_role(params["role"])

            elif action == "people_with_skill":
                data = self.get_people_with_skill(params["skill"])

            elif action == "project_members":
                data = self.get_project_members(params["project"])

            elif action == "suitable_for_project":
                data = self.is_person_suitable_for_project(
                    params["person"],
                    params["project"]
                )

            elif action == "raw_query":
                data = self.raw_query(params["query"])

            elif action == "explain_query":
                data = self.explain_query(params["query"])

            else:
                return {
                    "ok": False,
                    "error": f"Unbekannte Aktion: {action}"
                }

            return {
                "ok": True,
                "action": action,
                "data": data
            }

        except KeyError as exc:
            return {
                "ok": False,
                "error": f"Fehlender Parameter: {exc}"
            }

        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc)
            }