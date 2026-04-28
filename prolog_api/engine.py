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