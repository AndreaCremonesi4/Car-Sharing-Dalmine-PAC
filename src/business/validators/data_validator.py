"""
Validatore per integrità cache e coerenza dati.
"""

from dataclasses import dataclass
from typing import List
from src.data.models.studente import Studente
from src.data.repositories.cache_repository import CacheRepository


@dataclass
class ValidationResult:
    """Risultato validazione con dettaglio errori"""

    is_valid: bool
    errors: List[str]


class DataValidator:
    """
    Validatore per integrità cache e coerenza dati.
    Centralizza i controlli sparsi in modalita_ottimizza [file:1].
    """

    def __init__(self, comune_destinazione: str = "DALMINE"):  # <- AGGIUNTO
        self.destinazione = comune_destinazione

    def validate_cache_completeness(
        self, studenti: List[Studente], cache: CacheRepository
    ) -> ValidationResult:
        """
        Verifica che cache contenga tutti i dati necessari per ottimizzazione.
        """
        errors = []

        # Check 1: Coordinate
        localita_necessarie = {s.localita for s in studenti} | {self.destinazione}

        for loc in localita_necessarie:
            if not cache.coordinate_cache.has(loc):
                errors.append(f"Coordinate mancanti per: {loc}")
            elif cache.coordinate_cache.get(loc) is None:
                errors.append(f"Località non geocodificabile: {loc}")

        # Check 2: Percorsi verso destinazione
        for loc in localita_necessarie:
            if loc != self.destinazione:
                if not cache.percorsi_cache.has_complete(loc, self.destinazione):
                    errors.append(f"Percorso mancante: {loc} -> {self.destinazione}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
