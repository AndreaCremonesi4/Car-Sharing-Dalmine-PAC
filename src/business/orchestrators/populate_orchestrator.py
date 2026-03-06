"""
Orchestratore per modalità 'popola'.
Coordina download dati da API esterne e popolamento cache.
"""

from typing import List, Set
from itertools import permutations
from src.data.repositories.studenti_repository import StudentiRepository
from src.services.external_api_facade import ExternalAPIFacade
from src.business.clustering.base import ClusteringStrategy
from src.data.models.studente import Studente


class PopulateOrchestrator:
    """
    Orchestratore per modalità 'popola'.
    """

    def __init__(
        self,
        studenti_repo: StudentiRepository,
        api_facade: ExternalAPIFacade,
        clustering: ClusteringStrategy,
        comune_destinazione: str = "DALMINE",
    ):
        self.studenti_repo = studenti_repo
        self.api_facade = api_facade
        self.clustering = clustering
        self.cache = api_facade.cache
        self.destinazione = comune_destinazione

    def execute(self, batch_size: int = 1000):
        """
        Pipeline popolamento:
        1. Geocode località
        2. Clustering per identificare percorsi necessari
        3. Download percorsi in batch
        """
        print("=== MODALITÀ POPOLA ===\n")

        # Fase 1: Geocoding
        studenti = self.studenti_repo.load_studenti()
        self._geocode_localita(studenti)

        # Fase 2: Identificazione percorsi necessari
        studenti_validi = [s for s in studenti if s.coordinate]

        if len(studenti_validi) < self.clustering.n_clusters:
            raise ValueError(
                f"Studenti insufficienti ({len(studenti_validi)}) "
                f"per {self.clustering.n_clusters} cluster"
            )

        percorsi_necessari = self._identifica_percorsi_necessari(studenti_validi)

        # Fase 3: Download batch
        self._download_percorsi_batch(percorsi_necessari, batch_size)

        # Salvataggio finale
        self.cache.save_all()
        print("\n✓ Popolamento completato")

    def _geocode_localita(self, studenti: List[Studente]):
        """Geocode tutte le località uniche"""
        localita = {s.localita for s in studenti} | {self.destinazione}
        print(f"Geocoding {len(localita)} località...")

        for loc in localita:
            coords = self.api_facade.get_coordinate_with_cache(loc)
            for s in studenti:
                if s.localita == loc:
                    s.coordinate = coords

    def _identifica_percorsi_necessari(self, studenti: List[Studente]) -> Set[tuple]:
        """
        Usa clustering per identificare solo i percorsi realmente necessari.
        """
        clusters = self.clustering.cluster_studenti(studenti)

        percorsi_set = set()
        for cluster in clusters:
            localita = {s.localita for s in cluster} | {self.destinazione}
            # Tutte le coppie ordinate (permutazioni)
            for loc_a, loc_b in permutations(localita, 2):
                percorsi_set.add((loc_a, loc_b))

        return percorsi_set

    def _download_percorsi_batch(self, percorsi: Set[tuple], batch_size: int):
        """
        Download percorsi in batch con salvataggio incrementale.
        """
        # Filtra già presenti
        mancanti = [
            (a, b)
            for a, b in percorsi
            if not self.cache.percorsi_cache.has_complete(a, b)
        ]

        if not mancanti:
            print("✓ Cache percorsi già completa")
            return

        print(f"Percorsi mancanti: {len(mancanti)}")
        blocco = mancanti[:batch_size]
        print(f"Download batch di {len(blocco)} percorsi...")

        for i, (partenza, dest) in enumerate(blocco, 1):
            if i % 10 == 0:
                print(f"  Progresso: {i}/{len(blocco)}")
                self.cache.save_all()  # Salvataggio incrementale

            self.api_facade.get_percorso_with_cache(partenza, dest)

        rimanenti = len(mancanti) - len(blocco)
        if rimanenti > 0:
            print(f"\n⚠  Rimanenti: {rimanenti}. Riesegui per continuare.")
        else:
            print("\n✓ Tutti i percorsi scaricati")
