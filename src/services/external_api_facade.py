from typing import Optional, Tuple
from src.data.repositories import CacheRepository
from src.data.models.percorso import Percorso
from src.services.api.geocoding_service import GeocodingService
from src.services.api.routing_service import RoutingService


class ExternalAPIFacade:
    """
    Facade Pattern: interfaccia unificata per tutte le API esterne.
    Implementa la strategia "cache-first" per evitare chiamate inutili.

    """

    def __init__(
        self,
        geocoding: GeocodingService,
        routing: RoutingService,
        cache: CacheRepository,
    ):
        self.geocoding = geocoding
        self.routing = routing
        self.cache = cache

    def get_coordinate_with_cache(
        self, localita_key: str
    ) -> Optional[Tuple[float, float]]:
        """
        Ottiene coordinate con cache-first strategy.
        1. Controlla cache
        2. Se manca, chiama API
        3. Salva risultato in cache
        """
        # Check cache
        if self.cache.coordinate_cache.has(localita_key):
            return self.cache.coordinate_cache.get(localita_key)

        # Cache miss -> API call
        coords = self.geocoding.geocode_localita(localita_key)

        # Salva in cache (anche None se località non trovata)
        self.cache.coordinate_cache.set(localita_key, coords)

        return coords

    def get_percorso_with_cache(
        self, partenza_key: str, destinazione_key: str
    ) -> Optional[Percorso]:
        """
        Ottiene percorso con cache-first strategy.
        Gestisce anche il caso di località identiche (distanza 0).
        """
        # Caso speciale: stessa località
        if partenza_key == destinazione_key:
            return Percorso(
                partenza=partenza_key,
                destinazione=destinazione_key,
                durata_sec=0,
                distanza_m=0,
                geometria=[],
            )

        # Check cache
        if self.cache.percorsi_cache.has_complete(partenza_key, destinazione_key):
            return self.cache.percorsi_cache.get(partenza_key, destinazione_key)

        # Cache miss -> Serve geocoding prima
        start_coords = self.get_coordinate_with_cache(partenza_key)
        end_coords = self.get_coordinate_with_cache(destinazione_key)

        if not start_coords or not end_coords:
            print("Impossibile calcolare percorso: coordinate mancanti")
            return None

        # API call routing
        percorso = self.routing.calculate_route(
            start_coords, end_coords, partenza_key, destinazione_key
        )

        # Salva in cache se successo
        if percorso:
            self.cache.percorsi_cache.set(percorso)

        return percorso
