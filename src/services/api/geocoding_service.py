import time
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from src.data.repositories import ConfigRepository


class GeocodingService:
    """
    Adapter per servizi di geocoding (conversione indirizzo -> coordinate).
    Implementazione attuale: Nominatim (OpenStreetMap).
    """

    def __init__(self, config_repo: ConfigRepository, user_agent: str):
        self.config_repo = config_repo
        self.geolocator = Nominatim(user_agent=user_agent)

    def geocode_localita(self, localita_key: str) -> Optional[Tuple[float, float]]:
        """
        Converte chiave località in coordinate GPS.
        Gestisce automaticamente il contesto per quartieri di Bergamo.
        """
        # Ottieni nome formattato da repository
        nome = self.config_repo.get_localita_display_name(localita_key)
        if not nome:
            print(f"Warning: Località '{localita_key}' non mappata")
            return None

        # Costruisci query appropriata
        if self.config_repo.is_quartiere_bergamo(localita_key):
            query = f"{nome}, Bergamo, BG, Italia"
        else:
            query = f"{nome}, Italia"

        try:
            print(f"Geocoding: {query}")

            # Rate limiting (1 req/sec per Nominatim)
            time.sleep(1)

            location = self.geolocator.geocode(query, timeout=10)

            if location:
                return (location.latitude, location.longitude)
            else:
                print(f"Località non trovata: {query}")
                return None

        except Exception as e:
            print(f"Errore geocoding per {query}: {e}")
            return None
