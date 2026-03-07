from typing import List
from src.data.repositories import StudentiRepository
from src.data.repositories import CacheRepository
from ..validators.data_validator import DataValidator
from .optimization_facade import OptimizationFacade
from src.data.models import Equipaggio
from src.data.models import Percorso


class OptimizeOrchestrator:
    """
    Orchestratore per modalità 'ottimizza'.
    Esegue ottimizzazione offline usando dati in cache.
    """

    def __init__(
        self,
        studenti_repo: StudentiRepository,
        cache_repo: CacheRepository,
        validator: DataValidator,
        optimization_facade: OptimizationFacade,
    ):
        self.studenti_repo = studenti_repo
        self.cache = cache_repo
        self.validator = validator
        self.optimization = optimization_facade

    def execute(self) -> List[Equipaggio]:
        """
        Pipeline ottimizzazione:
        1. Validazione cache
        2. Caricamento dati
        3. Ottimizzazione
        """
        print("=== MODALITÀ OTTIMIZZA ===\n")

        # Fase 1: Validazione
        studenti = self.studenti_repo.load_studenti()
        validation_result = self.validator.validate_cache_completeness(
            studenti, self.cache
        )

        if not validation_result.is_valid:
            raise ValueError(
                "Cache incompleta. Errori:\n"
                + "\n".join(f"- {e}" for e in validation_result.errors)
                + "\n\nEsegui: python main.py popola"
            )

        print("✓ Cache validata\n")

        # Fase 2: Arricchimento studenti con coordinate
        for s in studenti:
            s.coordinate = self.cache.coordinate_cache.get(s.localita)

        # Fase 3: Ottimizzazione
        # Converti cache percorsi in dizionario per lookup veloce
        percorsi_dict = self._build_percorsi_dict()

        flotta = self.optimization.optimize_full(studenti, percorsi_dict)

        print(f"\n✓ Ottimizzazione completata: {len(flotta)} auto")
        return flotta

    def _build_percorsi_dict(self) -> dict:
        """Converte cache percorsi in dict per accesso O(1)"""
        percorsi = {}
        for key, data in self.cache.percorsi_cache.data.items():
            percorsi[key] = Percorso.from_cache_dict(key, data)
        return percorsi
