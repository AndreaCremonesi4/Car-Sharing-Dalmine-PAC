from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Studente:
    """Entità studente con dati anagrafici e coordinate."""

    email: str  # Identificatore univoco
    localita: str  # Chiave località (es. "BERGAMO")
    corso: str  # Corso di laurea (es. "INGEGNERIA")
    coordinate: Optional[Tuple[float, float]] = None  # (lat, lon) dopo geocoding

    def __post_init__(self):
        """Validazione e normalizzazione automatica"""
        self.email = self.email.lower()
        self.localita = self.localita.upper()
        self.corso = self.corso.upper()

    @property
    def localita_display(self) -> str:
        """Ritorna nome località formattato per visualizzazione"""
        # TODO: da implementare tramite ConfigRepository
        pass
