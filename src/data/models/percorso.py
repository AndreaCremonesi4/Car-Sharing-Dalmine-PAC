from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Percorso:
    """Rappresenta un percorso stradale tra due località."""

    partenza: str  # Chiave località partenza
    destinazione: str  # Chiave località destinazione
    durata_sec: int  # Tempo di percorrenza in secondi
    distanza_m: float  # Distanza in metri
    geometria: List[Tuple[float, float]]  # Lista coordinate [lon, lat] per mappa

    @property
    def durata_minuti(self) -> float:
        """Durata in minuti (comodo per stampe)"""
        return self.durata_sec / 60

    @property
    def distanza_km(self) -> float:
        """Distanza in chilometri"""
        return self.distanza_m / 1000

    @classmethod
    def from_cache_dict(cls, key: str, data: dict) -> "Percorso":
        """
        Factory method per creare Percorso da formato cache JSON.
        key formato: "PARTENZA-DESTINAZIONE"
        """
        partenza, destinazione = key.split("-")

        return cls(
            partenza=partenza,
            destinazione=destinazione,
            durata_sec=data.get("durata_sec"),
            distanza_m=data.get("distanza_m"),
            geometria=[(lon, lat) for lon, lat in data.get("geometria", [])],
        )
