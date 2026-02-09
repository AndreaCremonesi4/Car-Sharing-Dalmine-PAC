import requests
import time
import random
from typing import Optional
from src.data.models.percorso import Percorso


class RoutingService:
    """
    Adapter per servizi di routing (calcolo percorsi stradali).
    Implementazione attuale: OpenRouteService.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def calculate_route(
        self,
        start_coords: tuple[float, float],
        end_coords: tuple[float, float],
        start_key: str,
        end_key: str,
    ) -> Optional[Percorso]:
        """
        Calcola percorso stradale tra due coordinate.

        Args:
            start_coords: (lat, lon) partenza
            end_coords: (lat, lon) destinazione
            start_key: Chiave località partenza (per Percorso)
            end_key: Chiave località destinazione

        Returns:
            Percorso completo o None se errore.

        """
        # ORS vuole lon,lat
        params = {
            "api_key": self.api_key,
            "start": f"{start_coords[1]},{start_coords[0]}",
            "end": f"{end_coords[1]},{end_coords[0]}",
        }

        try:
            
            pausa = random.uniform(2, 5)
            print(f"Routing {start_key} -> {end_key} (pausa {pausa:.1f}s)")
            time.sleep(pausa)

            response = requests.get(self.base_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                summary = data["features"][0]["properties"]["summary"]
                geometry = data["features"][0]["geometry"]["coordinates"]

                return Percorso(
                    partenza=start_key,
                    destinazione=end_key,
                    durata_sec=int(summary["duration"]),
                    distanza_m=summary["distance"],
                    geometria=[(lon, lat) for lon, lat in geometry],
                )
            else:
                print(f"Errore API {response.status_code}: {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Errore connessione per {start_key}->{end_key}: {e}")
            return None
