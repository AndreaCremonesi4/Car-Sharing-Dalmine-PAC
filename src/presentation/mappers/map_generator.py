import folium
import random
from pathlib import Path
from typing import List
from src.data.models.equipaggio import Equipaggio
from src.data.repositories.cache_repository import CacheRepository


class MapGenerator:
    """
    Genera mappe HTML interattive con Folium.
    """

    def __init__(self, jitter_factor: float = 0.0003):
        self.jitter_factor = jitter_factor
        self.colori = [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "darkred",
            "lightred",
            "beige",
            "darkblue",
            "darkgreen",
            "cadetblue",
            "darkpurple",
            "pink",
            "lightblue",
            "gray",
            "black",
        ]

    def generate(
        self, flotta: List[Equipaggio], output_path: Path, cache: CacheRepository
    ):
        """
        Genera mappa HTML con percorsi e marker.

        Args:
            flotta: Lista equipaggi da visualizzare
            output_path: Percorso file HTML output
            cache: Repository per recuperare geometrie percorsi
        """
        # Centro mappa su Dalmine
        coords_dalmine = cache.coordinate_cache.get("DALMINE")
        if not coords_dalmine:
            coords_dalmine = (45.695, 9.67)  # Fallback

        mappa = folium.Map(location=coords_dalmine, zoom_start=11)

        # Marker destinazione
        folium.Marker(
            location=coords_dalmine,
            popup="<b>Destinazione</b><br>Dalmine",
            tooltip="Università",
            icon=folium.Icon(color="red", icon="university", prefix="fa"),
        ).add_to(mappa)

        # Disegna ogni equipaggio
        for equipaggio in flotta:
            self._add_equipaggio_to_map(mappa, equipaggio, cache)

        # Salva file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mappa.save(str(output_path))
        print(f"Mappa generata: {output_path}")

    def _add_equipaggio_to_map(self, mappa, equipaggio: Equipaggio, cache):
        """Aggiunge un equipaggio alla mappa (linee e marker)"""
        colore = self.colori[equipaggio.id % len(self.colori)]

        # Disegna percorso
        for i in range(len(equipaggio.percorso_tappe) - 1):
            partenza = equipaggio.percorso_tappe[i]
            arrivo = equipaggio.percorso_tappe[i + 1]

            percorso = cache.percorsi_cache.get(partenza, arrivo)
            if percorso and percorso.geometria:
                # Inverti lon,lat -> lat,lon per Folium
                coords_invertite = [(lat, lon) for lon, lat in percorso.geometria]

                folium.PolyLine(
                    locations=coords_invertite,
                    color=colore,
                    weight=5,
                    opacity=0.8,
                    tooltip=f"Auto {equipaggio.id}",
                ).add_to(mappa)

        # Marker passeggeri con jittering
        for membro in equipaggio.membri:
            coords = cache.coordinate_cache.get(membro.localita)
            if coords:
                lat_jitter = coords[0] + random.uniform(
                    -self.jitter_factor, self.jitter_factor
                )
                lon_jitter = coords[1] + random.uniform(
                    -self.jitter_factor, self.jitter_factor
                )

                folium.Marker(
                    location=(lat_jitter, lon_jitter),
                    popup=f"<b>{membro.email}</b><br>Da: {membro.localita}<br>Auto {equipaggio.id}",
                    tooltip=f"Auto {equipaggio.id}: {membro.email}",
                    icon=folium.Icon(color=colore, icon="user", prefix="fa"),
                ).add_to(mappa)
