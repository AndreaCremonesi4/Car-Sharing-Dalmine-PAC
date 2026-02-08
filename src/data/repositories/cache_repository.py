from pathlib import Path
import json
from typing import Optional, Dict, Tuple
from ..models import Percorso


class CacheRepository:
    """
    Repository principale per gestione cache.
    Coordina CoordinateCache e PercorsiCache.
    """

    def __init__(self, cache_dir: Path):
        coord_file = cache_dir / "cache_coordinate.json"
        percorsi_file = cache_dir / "cache_percorsi.json"

        self.coordinate_cache = CoordinateCache(coord_file)
        self.percorsi_cache = PercorsiCache(percorsi_file)

    def save_all(self):
        """Salva entrambe le cache su disco"""
        self.coordinate_cache.save()
        self.percorsi_cache.save()
        print("Cache salvate su disco")


class CoordinateCache:
    """
    Cache per coordinate geocodificate.
    Struttura: {"LOCALITA": [lat, lon] oppure null}
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data: Dict[str, Optional[Tuple[float, float]]] = self._load()

    def _load(self) -> dict:
        """Carica cache da file se esiste"""
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save(self):
        """Persiste cache su disco"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, localita_key: str) -> Optional[Tuple[float, float]]:
        """Recupera coordinate dalla cache"""
        coords = self.data.get(localita_key)
        if coords is None:
            return None
        return tuple(coords)

    def set(self, localita_key: str, coords: Optional[Tuple[float, float]]):
        """Salva coordinate in cache (o None se località non trovata)"""
        self.data[localita_key] = list(coords) if coords else None

    def has(self, localita_key: str) -> bool:
        """Verifica se località è già in cache (anche con valore None)"""
        return localita_key in self.data


class PercorsiCache:
    """
    Cache per percorsi stradali.
    Struttura: {"PARTENZA-DESTINAZIONE": {durata_sec, distanza_m, geometria}}
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data: Dict[str, dict] = self._load()

    def _load(self) -> dict:
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, partenza: str, destinazione: str) -> Optional[Percorso]:
        """
        Recupera percorso dalla cache come oggetto Percorso.
        Ritorna None se non presente o incompleto.
        """
        key = f"{partenza}-{destinazione}"
        data = self.data.get(key)

        if not data or "geometria" not in data:
            return None

        return Percorso.from_cache_dict(key, data)

    def set(self, percorso: Percorso):
        """Salva percorso in cache"""
        key = f"{percorso.partenza}-{percorso.destinazione}"
        self.data[key] = {
            "durata_sec": percorso.durata_sec,
            "distanza_m": percorso.distanza_m,
            "geometria": percorso.geometria,
        }

    def has_complete(self, partenza: str, destinazione: str) -> bool:
        """Verifica se percorso è in cache E ha la geometria completa"""
        key = f"{partenza}-{destinazione}"
        return key in self.data and "geometria" in self.data[key]
