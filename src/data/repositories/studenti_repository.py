from pathlib import Path
from typing import List
import json
from ..models.studente import Studente
from .config_repository import ConfigRepository


class StudentiRepository:
    """
    Repository per dati studenti.
    Legge da data/input/studenti.json.
    """

    def __init__(self, studenti_file: Path, config_repo: ConfigRepository):
        self.studenti_file = studenti_file
        self.config_repo = config_repo

    def load_studenti(self) -> List[Studente]:
        """Carica lista studenti da JSON di input."""
        if not self.studenti_file.exists():
            raise FileNotFoundError(f"File studenti non trovato: {self.studenti_file}")

        with open(self.studenti_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        studenti = []
        for i, studente in enumerate(data, 1):
            try:
                # Validazione implicita tramite dataclass
                studente = Studente(
                    email=studente["email"],
                    localita=studente["localita"],
                    corso=studente["corso"],
                )

                # Validazione località esistente
                if not self.config_repo.get_localita_display_name(studente.localita):
                    print(
                        f"Warning: Località sconosciuta '{studente.localita}' "
                        f"per studente {studente.email}"
                    )

                studenti.append(studente)

            except KeyError as e:
                print(f"Errore riga {i}: campo mancante {e}")
                continue

        return studenti
